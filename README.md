# Wonderland

_Like mixing MUD, classic chat room, and VRChat into a potent cocktail._

## List of Bugs

> Who needs a list of features when you have a big 'ol list of problems?

- The current system does not support multi-step commands.
  - For example, requesting username during login. Any input provided by the user will attempt to be matched to a command.
  - My naive first thought at resolving this is to create context windows which commands are limited during the window.
