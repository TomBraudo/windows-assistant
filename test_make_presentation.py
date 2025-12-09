"""
Manual test for the PowerPoint generation tool.

Run with:
    python test_make_presentation.py

This bypasses the LLM/agent and directly calls create_presentation.
"""

from app.tools.ppt_tools import create_presentation


def main():
    title = "Apache Kafka for Beginners"
    bullets = "\n".join(
        [
            "Title Slide: Apache Kafka for Beginners",
            "What is Apache Kafka?",
            "History and Evolution",
            "Core Concepts: topics, producers, consumers, brokers",
            "Kafka Architecture",
            "Producers and Consumers in Detail",
            "Use Cases",
            "Getting Started",
            "Conclusion",
        ]
    )

    # Simple image query to verify optional image insertion works end‑to‑end.
    # You can set image_query=None if you only want text slides.
    image_query = "Apache Kafka architecture diagram"

    result = create_presentation(
        title=title,
        bullet_text=bullets,
        filename="Kafka_for_Beginners_Test.pptx",
        image_query=image_query,
    )

    print(result)


if __name__ == "__main__":
    main()


