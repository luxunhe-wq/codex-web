# Plugins and skills

[中文说明](../README.md#插件与技能) | [English README](README.en.md)

Open **Plugins and skills** in the sidebar, or **Account and settings → Plugins and skills**.
The page lists installed plugins and skills available to the current conversation's project directory.
Enable/disable changes are saved in the server's Codex configuration and survive browser refreshes
and restarts. Wait for all web tasks to finish before changing these global settings; use a new
conversation after a change.

Choose **Use in conversation** on an enabled skill, finish writing your task and send it.
The composer inserts the skill name, and the website passes a native `skill` input to Codex as well
as your message. Skills are validated against the target project's current list before sending.
Removing the skill mention from the draft removes the explicit selection. Select a skill again
if you switch projects. Lists load only when the management page opens.

Install new plugins from the server terminal under the same user that runs the web service:

```sh
codex plugin --help
codex plugin list
# Replace plugin-name and marketplace-name with your configured marketplace's entries.
codex plugin add plugin-name@marketplace-name
```

For guided Docker deployments, run from the checkout:

```sh
docker compose --env-file .env.docker exec codex-web codex plugin list
docker compose --env-file .env.docker exec codex-web codex plugin add plugin-name@marketplace-name
```

Refresh the web list after installation. Docker stores installed plugins and their configuration
in the persistent `codex-config` volume; host plugins are not automatically imported.

The integration was verified with Codex 0.159.2. Unsupported plugin/skill APIs on older CLI versions
show an upgrade message without breaking conversations. Remote catalog access and third-party
application authentication depend on your Codex account and configuration. This release provides
installed plugin management and skill selection; a web marketplace browser, installation UI and
third-party application sign-in flow are not included.

For the upstream protocol, see the [official App Server documentation](https://developers.openai.com/codex/app-server/).
