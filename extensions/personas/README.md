# Personas Extension

This extension adds support for personas in the text-generation-webui. Personas allow you to save and switch between different combinations of:

- User name
- Character
- User description
- System prompt

## How to Use

### Setting up the extension

Enable the extension by:
- Adding `--extensions personas` to your command line when starting the server
- Or selecting it in the Extensions tab of the UI

### Creating and using personas

1. Configure your chat settings:
   - Select a character
   - Set your user name
   - Write your user description
   - Configure a system prompt

2. Click the "➕" button next to the Persona dropdown to save this configuration as a persona.

3. Use the Persona dropdown to select a saved persona:
   - The extension has auto-loading enabled by default (persona immediately loads when selected)
   - You can also click the "📂" button to manually load the selected persona if needed

4. Additional buttons:
   - 🔄 (Refresh) - Updates the list of available personas
   - 📂 (Load) - Manually loads the selected persona
   - ➕ (New) - Creates a new persona from the current settings

## Persona Files

Persona files are stored in the `personas` directory as JSON files with the following structure:

```json
{
  "user_name": "Morgan",
  "character_name": "Dexter Codewell",
  "user_description": "{{user}} is a software engineer...",
  "system_prompt": "You are an expert programming assistant..."
}
```

You can manually edit these files if needed, or create new ones by copying and modifying existing personas.

## Tips

- Create different personas for different use cases (coding, roleplay, writing, etc.)
- You can use the same character with different system prompts for different interaction styles
- User descriptions support the `{{user}}` placeholder which gets replaced with your name
- Personas are saved to disk, so they persist between sessions