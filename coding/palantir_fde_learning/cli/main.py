# cli/main.py
"""
Main CLI Application for FDE Learning System

This module implements the CLI using Click, providing commands for:
1. Profile Management: Create, view, update learner profiles
2. Recommendations: Get ZPD-based learning suggestions
3. Statistics: View progress and analytics
4. KB Operations: Browse and validate knowledge bases

Design Patterns:
- Click groups for hierarchical command structure
- Async support via asyncio.run()
- Dependency injection for repository/engine instances
- Rich output for better UX

Usage:
    fde-learn profile create --id user123
    fde-learn recommend --id user123 --limit 5
    fde-learn stats
    fde-learn kb list
"""

import asyncio
import click
from pathlib import Path
from typing import Optional
import json

from palantir_fde_learning.domain.types import (
    LearnerProfile,
    LearningDomain,
    DifficultyTier,
)
from palantir_fde_learning.adapters.repository.sqlite import SQLiteLearnerRepository
from palantir_fde_learning.adapters.kb_reader import KBReader
from palantir_fde_learning.application.scoping import ScopingEngine


# Default paths
DEFAULT_DB_PATH = "./data/learner_state.db"
DEFAULT_KB_PATH = "./palantir-fde-learning/knowledge_bases"


def get_repository(db_path: str) -> SQLiteLearnerRepository:
    """Factory for repository instance."""
    return SQLiteLearnerRepository(db_path)


def async_command(f):
    """Decorator to run async Click commands."""
    import functools
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper


# --- Main CLI Group ---

@click.group()
@click.option('--db', default=DEFAULT_DB_PATH, help='Path to SQLite database')
@click.option('--kb', default=DEFAULT_KB_PATH, help='Path to knowledge bases')
@click.pass_context
def app(ctx, db: str, kb: str):
    """
    Palantir FDE Learning System CLI.
    
    An adaptive learning tool for Palantir FDE interview preparation.
    Uses Zone of Proximal Development (ZPD) for personalized recommendations.
    """
    ctx.ensure_object(dict)
    ctx.obj['db_path'] = db
    ctx.obj['kb_path'] = kb


# --- Profile Commands ---

@app.group()
def profile():
    """Manage learner profiles."""
    pass


@profile.command('create')
@click.option('--id', 'learner_id', required=True, help='Unique learner identifier')
@click.pass_context
@async_command
async def profile_create(ctx, learner_id: str):
    """Create a new learner profile."""
    repo = get_repository(ctx.obj['db_path'])
    
    # Check if exists
    existing = await repo.find_by_id(learner_id)
    if existing:
        click.echo(f"Error: Profile '{learner_id}' already exists.", err=True)
        return
    
    profile = LearnerProfile(learner_id=learner_id)
    await repo.save(profile)
    click.echo(f"✓ Created profile: {learner_id}")


@profile.command('show')
@click.option('--id', 'learner_id', required=True, help='Learner identifier')
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON')
@click.pass_context
@async_command
async def profile_show(ctx, learner_id: str, as_json: bool):
    """Show learner profile details."""
    repo = get_repository(ctx.obj['db_path'])
    profile = await repo.find_by_id(learner_id)
    
    if not profile:
        click.echo(f"Error: Profile '{learner_id}' not found.", err=True)
        return
    
    if as_json:
        click.echo(profile.model_dump_json(indent=2))
    else:
        click.echo(f"\n📊 Profile: {profile.learner_id}")
        click.echo(f"   Overall Mastery: {profile.overall_mastery():.1%}")
        click.echo(f"   Concepts Studied: {len(profile.knowledge_states)}")
        
        mastered = profile.get_mastered_concepts()
        click.echo(f"   Mastered: {len(mastered)}")
        
        if profile.knowledge_states:
            click.echo("\n   Recent Progress:")
            for concept_id, state in list(profile.knowledge_states.items())[:5]:
                click.echo(f"   • {concept_id}: {state.mastery_level:.1%}")


@profile.command('list')
@click.option('--limit', default=20, help='Maximum profiles to show')
@click.pass_context
@async_command
async def profile_list(ctx, limit: int):
    """List all learner profiles."""
    repo = get_repository(ctx.obj['db_path'])
    profiles = await repo.find_all(limit=limit)
    
    if not profiles:
        click.echo("No profiles found.")
        return
    
    click.echo(f"\n📋 Learner Profiles ({len(profiles)} shown)")
    click.echo("-" * 50)
    for p in profiles:
        mastery = p.overall_mastery()
        concepts = len(p.knowledge_states)
        click.echo(f"  {p.learner_id:<20} {mastery:.1%} mastery  ({concepts} concepts)")


@profile.command('delete')
@click.option('--id', 'learner_id', required=True, help='Learner identifier')
@click.confirmation_option(prompt='Are you sure you want to delete this profile?')
@click.pass_context
@async_command
async def profile_delete(ctx, learner_id: str):
    """Delete a learner profile."""
    repo = get_repository(ctx.obj['db_path'])
    deleted = await repo.delete(learner_id)
    
    if deleted:
        click.echo(f"✓ Deleted profile: {learner_id}")
    else:
        click.echo(f"Error: Profile '{learner_id}' not found.", err=True)


# --- Recommendation Commands ---

@app.command('recommend')
@click.option('--id', 'learner_id', required=True, help='Learner identifier')
@click.option('--limit', default=5, help='Number of recommendations')
@click.option('--domain', 'domain_filter', default=None, help='Filter by domain (e.g., osdk, foundry)')
@click.pass_context
@async_command
async def recommend(ctx, learner_id: str, limit: int, domain_filter: Optional[str]):
    """Get personalized learning recommendations."""
    repo = get_repository(ctx.obj['db_path'])
    kb_path = ctx.obj['kb_path']
    
    # Load profile
    profile = await repo.find_by_id(learner_id)
    if not profile:
        click.echo(f"Error: Profile '{learner_id}' not found.", err=True)
        return
    
    # Load concept library from KBs
    try:
        reader = KBReader(kb_path)
        concepts = reader.build_concept_library()
    except Exception as e:
        click.echo(f"Error loading KBs: {e}", err=True)
        return
    
    # Get recommendations
    engine = ScopingEngine(concepts, profile)
    recs = engine.recommend_next_concept(limit=limit, domain_filter=domain_filter)
    
    if not recs:
        click.echo("No recommendations available. You may have mastered all concepts!")
        return
    
    click.echo(f"\n🎯 Recommended Concepts for {learner_id}")
    click.echo("-" * 60)
    for i, rec in enumerate(recs, 1):
        in_zpd = "✅ In ZPD" if rec.is_in_zpd() else "⚠️ Outside ZPD"
        click.echo(f"\n{i}. {rec.concept.title}")
        click.echo(f"   Domain: {rec.concept.domain.value}")
        click.echo(f"   Difficulty: {rec.concept.difficulty_tier.value}")
        click.echo(f"   Stretch Factor: {rec.stretch_factor:.0%}")
        click.echo(f"   Readiness: {rec.readiness_score:.0%}")
        click.echo(f"   Status: {in_zpd}")


# --- Statistics Commands ---

@app.command('stats')
@click.pass_context
@async_command
async def stats(ctx):
    """Show overall learning statistics."""
    repo = get_repository(ctx.obj['db_path'])
    statistics = await repo.get_statistics()
    
    click.echo("\n📈 Learning System Statistics")
    click.echo("-" * 40)
    click.echo(f"Total Learners: {statistics['total_learners']}")
    click.echo(f"Average Mastery: {statistics['average_mastery']:.1%}")
    click.echo(f"Active Learners: {statistics['active_count']}")
    click.echo(f"Stale Profiles (>7 days): {statistics['stale_count']}")
    
    if statistics.get('distribution'):
        click.echo("\nMastery Distribution:")
        for tier, count in statistics['distribution'].items():
            click.echo(f"  • {tier}: {count}")


# --- KB Commands ---

@app.group()
def kb():
    """Knowledge base operations."""
    pass


@kb.command('list')
@click.pass_context
def kb_list(ctx):
    """List available knowledge bases."""
    kb_path = ctx.obj['kb_path']
    
    try:
        reader = KBReader(kb_path)
        docs = reader.scan_directory()
    except Exception as e:
        click.echo(f"Error scanning KBs: {e}", err=True)
        return
    
    if not docs:
        click.echo("No knowledge bases found.")
        return
    
    click.echo(f"\n📚 Knowledge Bases ({len(docs)} found)")
    click.echo("-" * 60)
    for doc in docs:
        score = doc.completeness_score()
        status = "✅" if score >= 0.8 else "⚠️"
        click.echo(f"  {status} {doc.title}")
        click.echo(f"     Domain: {doc.domain.value if doc.domain else 'Unknown'}")
        click.echo(f"     Completeness: {score:.0%}")


@kb.command('validate')
@click.pass_context
def kb_validate(ctx):
    """Validate all knowledge bases."""
    kb_path = ctx.obj['kb_path']
    
    try:
        reader = KBReader(kb_path)
        docs = reader.scan_directory()
    except Exception as e:
        click.echo(f"Error scanning KBs: {e}", err=True)
        return
    
    click.echo(f"\n🔍 Validating {len(docs)} Knowledge Bases")
    click.echo("-" * 60)
    
    issues = []
    for doc in docs:
        score = doc.completeness_score()
        missing = [s for s in reader.KB_SECTIONS if not doc.has_section(s)]
        
        if missing:
            issues.append((doc.title, missing))
            click.echo(f"⚠️ {doc.title}")
            click.echo(f"   Missing sections: {', '.join(missing)}")
        else:
            click.echo(f"✅ {doc.title}")
    
    if issues:
        click.echo(f"\n⚠️ {len(issues)} KB(s) have missing sections")
    else:
        click.echo(f"\n✅ All KBs are complete!")


# --- Entry Point ---

def main():
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
