# server/app/services/ollama_service.py
import ollama
import logging
import asyncio
import json

logger = logging.getLogger(__name__)

# --- Configuration ---
OLLAMA_MODEL = "phi3:3.8b"
DEFAULT_OPTIONS = {
    'temperature': 0.2, # Lower for more focused outputs
    'top_p': 0.9,
    'num_predict': 1000, # Adjust based on needs/model capacity
}

async def query_llm(prompt: str, model: str = OLLAMA_MODEL, options: dict = None) -> str:
    """
    Queries the locally running Ollama model.

    Args:
        prompt: The prompt string to send to the model.
        model: The Ollama model name.
        options: A dictionary of options to pass to ollama.generate.

    Returns:
        The generated text response from the model, or an error message string.
    """
    if options is None:
        options = DEFAULT_OPTIONS
    else:
        merged_options = DEFAULT_OPTIONS.copy()
        merged_options.update(options)
        options = merged_options

    try:
        logger.debug(f"Sending prompt to Ollama model {model}...")
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: ollama.generate(
                model=model,
                prompt=prompt,
                options=options,
            )
        )

        generated_text = response.get('response', '').strip()

        if not generated_text:
            logger.warning(f"Ollama response seems empty or unexpected format: {response}")
            return "LLM response was empty or malformed."

        logger.debug(f"Received response from Ollama: {generated_text[:100]}...")
        return generated_text

    except Exception as e:
        error_msg = f"LLM Query Error (Ollama): {str(e)}"
        logger.error(error_msg)
        return error_msg

def extract_structured_info(full_article_text: str, model: str = OLLAMA_MODEL, options: dict = None) -> dict:
    """
    Uses the local Ollama model to extract structured information from text.
    Returns a dictionary with the extracted information.
    """
    if not full_article_text.strip():
        logger.warning("Empty article text provided for LLM extraction.")
        return {}

    # --- Prompt Engineering ---
    prompt = f"""
    <|start_of_turn|>user
    Analyze the following fact-checking article and extract the requested information.

    Instructions:
    1.  Read the article carefully.
    2.  Extract only the information explicitly stated or strongly implied.
    3.  Respond ONLY with a single, valid JSON object. No other text, no explanations, no markdown code blocks (no ```json ... ```), no <think> tags.
    4.  If information for a category is not found, leave the field empty (e.g., "", [], "Not Specified").
    5.  Ensure the JSON is correctly formatted (valid keys, values, quotes, commas, braces).

    Article Text:
    {full_article_text}

    JSON Structure:
    {{
      "core_claim": "The main claim being investigated.",
      "verdict": "The fact-checker's final verdict/rating (e.g., True, False, Mostly True).",
      "originated_from": "Where did the claim originate? (e.g., Social media post, News article, Person, Website). If multiple origins, list them.",
      "originator": "Who originally made the claim? (e.g., Specific person's name, Organization, Username).",
      "shared_by": "Who shared or amplified the claim after its origin? (e.g., Specific person, Organization, Type of platform).",
      "spreaders": "Who is identified as spreading the claim, especially if negatively characterized? (e.g., Misinformation groups, Specific individuals).",
      "entities_involved": [
        {{
          "name": "Entity Name 1",
          "type": "person|organization|place|other",
          "role": "Role in the claim or article"
        }},
        {{
          "name": "Entity Name 2",
          "type": "person|organization|place|other",
          "role": "Role in the claim or article"
        }}
      ],
      "key_evidence": [
        "Key evidence point 1...",
        "Key evidence point 2..."
      ],
      "relevant_context": "Important background context provided by the article relevant to understanding the claim or verdict.",
      "implications": "What are the potential consequences or implications of the claim being true/false, as discussed in the article? (Optional)"
    }}
    <|end_of_turn|>
    <|start_of_turn|>model
    """

    response_text = asyncio.run(query_llm(prompt, model=model, options=options))

    if response_text.startswith("LLM Query Error"):
        logger.error(f"Skipping JSON parsing due to LLM error: {response_text}")
        return {}

    if not response_text.strip():
        logger.warning("Received empty response from LLM for structured extraction.")
        return {}
    
    # --- Attempt Cleanup ---
    cleaned_response = response_text.strip()
    # Find the first '{' and last '}'
    start_idx = cleaned_response.find('{')
    end_idx = cleaned_response.rfind('}')
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
         potential_json_str = cleaned_response[start_idx:end_idx+1]
         # Optional: Add basic validation or logging if cleaned
         # logger.debug(f"Attempting to parse cleaned JSON: {potential_json_str[:100]}...")
    else:
         potential_json_str = cleaned_response # Fallback if {} not found
         logger.warning(f"Could not clearly identify JSON boundaries in LLM response. Trying to parse full response.")

    try:
        structured_info = json.loads(potential_json_str)
        logger.info("Successfully parsed LLM JSON response.")
        return structured_info
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing LLM JSON response: {e}. Raw response was: {response_text}")
        return {}
