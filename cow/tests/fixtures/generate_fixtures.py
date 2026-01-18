"""
Test fixture generator for Math Image Parsing Pipeline E2E tests.

Generates test images using matplotlib for various mathematical content types:
- Simple equations
- Quadratic/function graphs
- Geometry diagrams
- Complex calculus expressions
- Handwritten-style math

Usage:
    python -m tests.fixtures.generate_fixtures

Or import and use programmatically:
    from tests.fixtures.generate_fixtures import generate_all_fixtures
    generate_all_fixtures()
"""

import os
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Polygon
import numpy as np


# Output directory for generated images
FIXTURES_DIR = Path(__file__).parent / "images"


def ensure_output_dir() -> Path:
    """Ensure the output directory exists."""
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    return FIXTURES_DIR


def generate_simple_equation(output_path: Optional[Path] = None) -> Path:
    """
    Generate a simple linear equation image: y = 2x + 3

    Creates a clean, printed-style equation suitable for OCR testing.

    Returns:
        Path to the generated image file.
    """
    if output_path is None:
        output_path = ensure_output_dir() / "simple_equation.png"

    fig, ax = plt.subplots(figsize=(6, 2), dpi=150)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    # Title/context text
    ax.text(0.5, 0.75, "Find the value of y when x = 5:",
            fontsize=14, ha='center', va='center',
            fontfamily='serif')

    # Main equation
    ax.text(0.5, 0.35, r"$y = 2x + 3$",
            fontsize=24, ha='center', va='center',
            fontfamily='serif', math_fontfamily='cm')

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)

    return output_path


def generate_quadratic_graph(output_path: Optional[Path] = None) -> Path:
    """
    Generate a quadratic function graph: y = x^2 with labels.

    Creates a parabola with axis labels, grid, and equation label.

    Returns:
        Path to the generated image file.
    """
    if output_path is None:
        output_path = ensure_output_dir() / "quadratic_graph.png"

    fig, ax = plt.subplots(figsize=(8, 6), dpi=150)

    # Generate parabola data
    x = np.linspace(-3, 3, 100)
    y = x ** 2

    # Plot the parabola
    ax.plot(x, y, 'b-', linewidth=2, label=r'$y = x^2$')

    # Add grid
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.axhline(y=0, color='k', linewidth=0.5)
    ax.axvline(x=0, color='k', linewidth=0.5)

    # Add labels
    ax.set_xlabel('x', fontsize=14)
    ax.set_ylabel('y', fontsize=14)
    ax.set_title('Quadratic Function', fontsize=16)

    # Add equation label in corner
    ax.text(0.95, 0.95, r'$y = x^2$',
            transform=ax.transAxes, fontsize=16,
            verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # Mark key points
    ax.plot(0, 0, 'ro', markersize=8)  # Vertex
    ax.annotate('Vertex (0, 0)', xy=(0, 0), xytext=(0.5, 1),
                fontsize=10, arrowprops=dict(arrowstyle='->', color='red'))

    ax.plot(1, 1, 'go', markersize=6)
    ax.annotate('(1, 1)', xy=(1, 1), xytext=(1.5, 2),
                fontsize=10, arrowprops=dict(arrowstyle='->', color='green'))

    ax.plot(-1, 1, 'go', markersize=6)
    ax.annotate('(-1, 1)', xy=(-1, 1), xytext=(-2, 2),
                fontsize=10, arrowprops=dict(arrowstyle='->', color='green'))

    ax.set_xlim(-3.5, 3.5)
    ax.set_ylim(-0.5, 9.5)
    ax.legend(loc='upper left')

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)

    return output_path


def generate_geometry_diagram(output_path: Optional[Path] = None) -> Path:
    """
    Generate a geometry diagram: Triangle ABC with labeled vertices.

    Creates a triangle with vertices A, B, C and side length annotations.

    Returns:
        Path to the generated image file.
    """
    if output_path is None:
        output_path = ensure_output_dir() / "geometry_diagram.png"

    fig, ax = plt.subplots(figsize=(8, 6), dpi=150)
    ax.set_xlim(-0.5, 5.5)
    ax.set_ylim(-0.5, 5)
    ax.set_aspect('equal')
    ax.axis('off')

    # Triangle vertices
    A = np.array([2.5, 4.5])  # Top vertex
    B = np.array([0.5, 0.5])  # Bottom left
    C = np.array([4.5, 0.5])  # Bottom right

    # Draw triangle
    triangle = Polygon([A, B, C], fill=False, edgecolor='blue', linewidth=2)
    ax.add_patch(triangle)

    # Draw vertices as points
    for point, label, offset in [(A, 'A', (0, 0.3)),
                                  (B, 'B', (-0.3, -0.3)),
                                  (C, 'C', (0.3, -0.3))]:
        ax.plot(point[0], point[1], 'ko', markersize=8)
        ax.text(point[0] + offset[0], point[1] + offset[1], label,
                fontsize=16, ha='center', va='center', fontweight='bold')

    # Add side length labels
    # Side AB
    mid_AB = (A + B) / 2
    ax.text(mid_AB[0] - 0.4, mid_AB[1], 'c', fontsize=12, ha='center', va='center',
            style='italic', color='darkblue')

    # Side BC
    mid_BC = (B + C) / 2
    ax.text(mid_BC[0], mid_BC[1] - 0.35, 'a', fontsize=12, ha='center', va='center',
            style='italic', color='darkblue')

    # Side CA
    mid_CA = (C + A) / 2
    ax.text(mid_CA[0] + 0.4, mid_CA[1], 'b', fontsize=12, ha='center', va='center',
            style='italic', color='darkblue')

    # Add angle arc at vertex B
    angle_arc = patches.Arc(B, 0.8, 0.8, angle=0, theta1=0, theta2=63.43,
                            color='red', linewidth=1.5)
    ax.add_patch(angle_arc)
    ax.text(B[0] + 0.6, B[1] + 0.35, r'$\theta$', fontsize=12, color='red')

    # Add title and formula
    ax.text(2.5, -0.2, 'Triangle ABC', fontsize=14, ha='center', va='center',
            fontweight='bold')
    ax.text(2.5, 5.2, r'Area $= \frac{1}{2} \times base \times height$',
            fontsize=12, ha='center', va='center')

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)

    return output_path


def generate_complex_calculus(output_path: Optional[Path] = None) -> Path:
    """
    Generate a complex calculus expression with integral and limits.

    Creates an image with a definite integral, derivative, and limit notation.

    Returns:
        Path to the generated image file.
    """
    if output_path is None:
        output_path = ensure_output_dir() / "complex_calculus.png"

    fig, ax = plt.subplots(figsize=(10, 4), dpi=150)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    # Problem statement
    ax.text(0.5, 0.85, "Evaluate the following integral:",
            fontsize=14, ha='center', va='center', fontfamily='serif')

    # Main integral expression
    integral_expr = r"$\int_{0}^{\pi} \sin^2(x) \, dx = \frac{\pi}{2}$"
    ax.text(0.5, 0.55, integral_expr,
            fontsize=28, ha='center', va='center',
            fontfamily='serif', math_fontfamily='cm')

    # Additional context - derivative relation
    ax.text(0.5, 0.2, r"Using: $\sin^2(x) = \frac{1 - \cos(2x)}{2}$",
            fontsize=16, ha='center', va='center',
            fontfamily='serif', math_fontfamily='cm')

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)

    return output_path


def generate_handwritten_math(output_path: Optional[Path] = None) -> Path:
    """
    Generate a handwritten-style math expression.

    Creates an image that simulates handwritten mathematical notation
    using a handwriting-style font and slight variations.

    Returns:
        Path to the generated image file.
    """
    if output_path is None:
        output_path = ensure_output_dir() / "handwritten_math.png"

    fig, ax = plt.subplots(figsize=(8, 4), dpi=150)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    # Set a background that looks like paper
    fig.patch.set_facecolor('#fffef0')
    ax.set_facecolor('#fffef0')

    # Add some "ruled lines" like notebook paper
    for y in np.arange(0.1, 1.0, 0.15):
        ax.axhline(y=y, color='#e0e0e0', linewidth=0.5, linestyle='-')

    # Use a more casual font style
    # Note: For true handwriting, you'd need a handwriting font installed
    # This simulates it with slight positioning variations

    # Problem number
    ax.text(0.05, 0.85, "1)", fontsize=14, ha='left', va='center',
            fontfamily='serif', style='italic')

    # Solve for x
    ax.text(0.12, 0.85, "Solve for x:", fontsize=14, ha='left', va='center',
            fontfamily='serif')

    # Equation (slightly tilted to simulate handwriting)
    ax.text(0.25, 0.65, r"$3x + 7 = 22$", fontsize=20, ha='left', va='center',
            fontfamily='serif', math_fontfamily='cm', rotation=1)

    # Solution steps
    ax.text(0.25, 0.45, r"$3x = 22 - 7$", fontsize=18, ha='left', va='center',
            fontfamily='serif', math_fontfamily='cm', rotation=-0.5)

    ax.text(0.25, 0.28, r"$3x = 15$", fontsize=18, ha='left', va='center',
            fontfamily='serif', math_fontfamily='cm', rotation=0.5)

    # Final answer with box
    ax.text(0.25, 0.1, r"$x = 5$", fontsize=20, ha='left', va='center',
            fontfamily='serif', math_fontfamily='cm',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.3))

    # Add a checkmark
    ax.text(0.55, 0.1, r'$\checkmark$', fontsize=20, ha='left', va='center',
            color='green')

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', facecolor='#fffef0', edgecolor='none')
    plt.close(fig)

    return output_path


def generate_trigonometric_graph(output_path: Optional[Path] = None) -> Path:
    """
    Generate a trigonometric function graph with sin and cos.

    Returns:
        Path to the generated image file.
    """
    if output_path is None:
        output_path = ensure_output_dir() / "trig_graph.png"

    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)

    # Generate data
    x = np.linspace(-2 * np.pi, 2 * np.pi, 500)
    y_sin = np.sin(x)
    y_cos = np.cos(x)

    # Plot functions
    ax.plot(x, y_sin, 'b-', linewidth=2, label=r'$y = \sin(x)$')
    ax.plot(x, y_cos, 'r--', linewidth=2, label=r'$y = \cos(x)$')

    # Add grid and axes
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.axhline(y=0, color='k', linewidth=0.5)
    ax.axvline(x=0, color='k', linewidth=0.5)

    # Set x-axis ticks to multiples of pi
    ax.set_xticks([-2*np.pi, -np.pi, 0, np.pi, 2*np.pi])
    ax.set_xticklabels([r'$-2\pi$', r'$-\pi$', '0', r'$\pi$', r'$2\pi$'])

    ax.set_xlabel('x', fontsize=14)
    ax.set_ylabel('y', fontsize=14)
    ax.set_title('Trigonometric Functions', fontsize=16)
    ax.legend(loc='upper right', fontsize=12)

    ax.set_xlim(-2.5 * np.pi, 2.5 * np.pi)
    ax.set_ylim(-1.5, 1.5)

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)

    return output_path


def generate_all_fixtures() -> dict[str, Path]:
    """
    Generate all test fixture images.

    Returns:
        Dictionary mapping fixture names to their file paths.
    """
    ensure_output_dir()

    fixtures = {
        "simple_equation": generate_simple_equation(),
        "quadratic_graph": generate_quadratic_graph(),
        "geometry_diagram": generate_geometry_diagram(),
        "complex_calculus": generate_complex_calculus(),
        "handwritten_math": generate_handwritten_math(),
        "trig_graph": generate_trigonometric_graph(),
    }

    print(f"Generated {len(fixtures)} fixture images:")
    for name, path in fixtures.items():
        print(f"  - {name}: {path}")

    return fixtures


def get_fixture_path(fixture_name: str) -> Path:
    """
    Get the path to a specific fixture image.

    Args:
        fixture_name: Name of the fixture (e.g., "simple_equation")

    Returns:
        Path to the fixture image file.

    Raises:
        FileNotFoundError: If the fixture doesn't exist.
    """
    fixture_map = {
        "simple_equation": "simple_equation.png",
        "quadratic_graph": "quadratic_graph.png",
        "geometry_diagram": "geometry_diagram.png",
        "complex_calculus": "complex_calculus.png",
        "handwritten_math": "handwritten_math.png",
        "trig_graph": "trig_graph.png",
    }

    if fixture_name not in fixture_map:
        raise ValueError(f"Unknown fixture: {fixture_name}. "
                        f"Available: {list(fixture_map.keys())}")

    path = FIXTURES_DIR / fixture_map[fixture_name]

    if not path.exists():
        # Generate the fixture if it doesn't exist
        print(f"Fixture {fixture_name} not found, generating...")
        generate_all_fixtures()

    return path


if __name__ == "__main__":
    generate_all_fixtures()
