"""
OpenAI API utilities for AI Research Script
"""

import os
import sys
import logging
from openai import OpenAI


def get_openai_client(logger: logging.Logger) -> OpenAI:
    """Initialize and return OpenAI client."""
    logger.info("Initializing OpenAI client...")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set.")
        logger.error("Please set it with: export OPENAI_API_KEY='your-api-key'")
        sys.exit(1)
    logger.info("OpenAI client initialized successfully")
    return OpenAI(api_key=api_key)


def call_openai(client: OpenAI, prompt: str, logger: logging.Logger, model: str = None, enable_web_search: bool = True) -> str:
    """Call OpenAI's Responses API with web browsing if enabled."""
    # Get model and web search settings from environment or use defaults
    if model is None:
        model = os.getenv("OPENAI_MODEL", "gpt-5.2")
    
    if enable_web_search is None:
        enable_web_search = os.getenv("WEB_SEARCH", "true").lower() == "true"
    
    logger.info(f"Calling OpenAI API with model: {model}...")
    
    try:
        # Use Responses API (same as ChatGPT UI) with web search tool if enabled
        if enable_web_search:
            logger.info("Using Responses API with web browsing enabled...")
            response = client.responses.create(
                model=model,
                input=prompt,
                tools=[{"type": "web_search"}],  # Enable web browsing (same as ChatGPT UI)
                include=["web_search_call.action.sources"],  # Optional: return sources
            )
            logger.info("Web browsing enabled successfully!")
            result = response.output_text
            logger.info(f"OpenAI API call completed successfully ({len(result)} characters returned)")
            return result
        else:
            # Fallback to Chat Completions API if web browsing is disabled
            logger.info("Using Chat Completions API (web browsing disabled)...")
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            )
            result = response.choices[0].message.content
            logger.info(f"OpenAI API call completed successfully ({len(result)} characters returned)")
            return result
    except AttributeError as e:
        # Responses API might not be available in older library versions
        if "responses" in str(e).lower():
            logger.warning("Responses API not available in this OpenAI library version.")
            logger.warning("Falling back to Chat Completions API...")
            logger.warning("To enable web browsing, update: pip install --upgrade openai")
            # Fallback to chat completions
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            )
            result = response.choices[0].message.content
            logger.info(f"Fallback API call completed successfully ({len(result)} characters returned)")
            return result
        else:
            raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error calling OpenAI API: {e}", exc_info=True)
        
        # Provide helpful suggestions for common errors
        if "model" in error_msg.lower() and ("not exist" in error_msg.lower() or "not found" in error_msg.lower()):
            logger.error("\nSuggested fixes:")
            logger.error("1. Check if the model name is correct. Available models include:")
            logger.error("   - gpt-5.2 (recommended for research with web browsing)")
            logger.error("   - gpt-4o (widely available, no browsing)")
            logger.error("   - gpt-4-turbo")
            logger.error("   - gpt-4")
            logger.error("2. Set OPENAI_MODEL in your .env file, e.g.:")
            logger.error("   OPENAI_MODEL=gpt-5.2")
            logger.error("3. To enable web browsing:")
            logger.error("   - Update OpenAI library: pip install --upgrade openai")
            logger.error("   - Ensure your account has Responses API access")
            logger.error("   - Set WEB_SEARCH=true in .env (default)")
        elif "responses" in error_msg.lower():
            logger.warning("\nNote: Responses API may require:")
            logger.warning("   - Updated OpenAI library: pip install --upgrade openai")
            logger.warning("   - Account access to Responses API")
            logger.warning("   - Falling back to Chat Completions API without browsing...")
            # Try fallback
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                )
                result = response.choices[0].message.content
                logger.info(f"Fallback API call completed successfully ({len(result)} characters returned)")
                return result
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}", exc_info=True)
                sys.exit(1)
        
        sys.exit(1)
