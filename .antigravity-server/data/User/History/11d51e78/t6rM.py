import json
import sys
import os

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from lib.digital_twin.schema import DigitalTwin, Block, Content, Style, Geometry, Page

def create_sample_twin() -> DigitalTwin:
    """Creates a mock Digital Twin for demonstration."""
    return DigitalTwin(
        document_id="doc_2504_sample",
        pages=[
            Page(
                page_num=1,
                blocks=[
                    # Header
                    Block(
                        id="p1_b1",
                        type="header",
                        role="title",
                        content=Content(text="Quadratic Equations Check"),
                        style=Style(font_size="18pt", font_weight="bold", alignment="center"),
                        geometry=Geometry(page_num=1, bbox=[10, 5, 80, 10])
                    ),
                    # Question 1 (Text + Math)
                    Block(
                        id="p1_b2",
                        type="math",
                        role="question",
                        content=Content(
                            text_pre="1. Solve for x:",
                            latex="x^2 - 4x + 4 = 0"
                        ),
                        style=Style(margin_bottom="10mm", padding="5mm"),
                        geometry=Geometry(page_num=1, bbox=[10, 20, 80, 15])
                    ),
                    # Question 2 (Typo to be fixed)
                    Block(
                        id="p1_b3",
                        type="math",
                        role="question",
                        content=Content(
                            text_pre="2. Find the roots:",
                            latex="x^2 + 5x + 6 = 1" # Intentional 'error' for demo
                        ),
                        style=Style(margin_bottom="10mm", padding="5mm"),
                        geometry=Geometry(page_num=1, bbox=[10, 40, 80, 15])
                    )
                ]
            )
        ]
    )

def main():
    print("--- 1. LOADING DIGITAL TWIN ---")
    twin = create_sample_twin()
    print(f"Loaded Doc ID: {twin.document_id}")
    print(f"Blocks: {len(twin.pages[0].blocks)}")
    
    # Snapshot before
    q2 = twin.get_block("p1_b3")
    print(f"\n[Before Edit] Q2 Latex: {q2.content.latex}")
    print(f"[Before Edit] Q2 Padding: {q2.style.padding}")

    print("\n--- 2. EXECUTING SCENARIO A: Content Modification ---")
    print("User Command: 'Fix the typo in Q2 (set to = 0)'")
    # Logic: Direct ID access or search
    target = twin.get_block("p1_b3")
    if target:
        target.content.latex = "x^2 + 5x + 6 = 0"
        print(f"Updated Q2 Latex: {target.content.latex}")

    print("\n--- 3. EXECUTING SCENARIO B: Layout Adjustment ---")
    print("User Command: 'Increase padding for all questions to 10mm'")
    # Logic: Query and Update
    questions = twin.query_blocks(role="question")
    for q in questions:
        q.style.padding = "10mm"
        print(f"Updated {q.id} Padding: {q.style.padding}")

    print("\n--- 4. EXECUTING SCENARIO C: Export Simulation ---")
    # Mock Export
    print("Exporting to Markdown...")
    markdown_out = f"# {twin.pages[0].blocks[0].content.text}\n\n"
    for block in twin.pages[0].blocks:
        if block.role == "question":
            markdown_out += f"**Question:** {block.content.latex}\n"
    
    print(markdown_out)
    print("--- DEMO COMPLETE ---")

if __name__ == "__main__":
    main()
