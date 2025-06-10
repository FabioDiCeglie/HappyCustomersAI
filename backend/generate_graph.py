from app.agents.review_agent import create_review_analysis_graph
import os

def generate_image():
    """Generates a PNG image of the LangGraph workflow."""
    print("Generating graph image...")
    graph = create_review_analysis_graph()

    try:
        # The get_graph().draw_mermaid_png() method generates the image bytes.
        image_bytes = graph.get_graph().draw_mermaid_png()

        # Define the output path
        output_filename = "review_analysis_graph.png"
        
        # Save the image
        with open(output_filename, "wb") as f:
            f.write(image_bytes)

        print(f"✅ Graph image saved to: {os.path.abspath(output_filename)}")
        print("You can now open this file to view the graph.")

    except Exception as e:
        print(f"❌ Error generating graph image: {e}")
        print("\\nIt seems there was an issue generating the PNG. This can happen if required system dependencies for rendering are missing (like a browser for mermaid.js).")
        print("\\nAs an alternative, here is the MermaidJS markdown for the graph. You can copy and paste this into a MermaidJS viewer (like https://mermaid.live):")
        try:
            mermaid_markdown = graph.get_graph().draw_mermaid()
            print("\\n--- Mermaid Markdown ---")
            print(mermaid_markdown)
            print("------------------------\\n")
        except Exception as e2:
            print(f"Could not even generate Mermaid markdown: {e2}")


if __name__ == "__main__":
    generate_image() 