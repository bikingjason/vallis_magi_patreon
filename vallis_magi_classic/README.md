# Vallis Magi Classic - A Rogue Lite

This repository is an implementation based on the classic Rogue design. I have called it Classic but a Rogue Lite as I do not plan to limit myself to a rigorous Rogue Like implementation as defined by the Berlin interpretation: <https://en.wikipedia.org/wiki/Roguelike#Key_features>

My plan is to use a C implementation I found in GitHub as a reference guide, but all the code will be my mine albeit developed with the assistance of some LLMs, most likely ChatGPT, GitHub Co-pilot and a locally run LLM.

Please see the [[README]] for details of the licensing and the reference repository.

# CLI Arguments

| Option | Type | Default | Help |
|---|---|---:|---|
| `--terse` | `bool` | `False` | Terse output. |
| `--flush` | `bool` | `False` | Flush typeahead during battle. |
| `--jump` | `bool` | `True` | Show position only at end of run. |
| `--step` | `bool` | `False` | Do inventories one line at a time. |
| `--askme` | `bool` | `False` | Ask me about unidentified things. |
| `--showac` | `bool` | `False` | Show armour class instead of protection. |
| `--name` | `str` | `""` | User's name. |
| `--fruit` | `str` | `""` | Name of favourite fruit. |
| `--file` | `str` | `"vmclassic.toml"` | Save file name. |

