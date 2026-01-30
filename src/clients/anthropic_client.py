import anthropic


class AnthropicClient:
    def __init__(self) -> None:
        self._client = anthropic.Anthropic(
            base_url="http://localhost:11434",
            api_key="ollama",  # required but ignored
        )

    def generate_message(
        self,
        user_content: str,
        system_prompt: str,
        max_tokens: int = 8000,
    ) -> str:
        message = self._client.messages.create(
            model="glm-4.7-flash",
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )
        # Extract text from text blocks, skipping thinking blocks
        text_parts = []
        for block in message.content:
            if block.type == "text":
                text_parts.append(block.text)
        return "".join(text_parts).strip()
