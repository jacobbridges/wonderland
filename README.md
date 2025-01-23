# Wonderland

> Text-based persistent world with websockets and Carroll.

## Architecture Diagrams

_Because sometimes it helps to picture it in your mind._

### High Level Overview

![High Level Diagram](docs/media/high-level-overview.png)

### Pipe Internals

![What's happening in a Pipe?](docs/media/whats-happening-in-a-pipe.png)



## List of Bugs

> Who needs a list of features when you have a big 'ol list of problems?

- The current system does not support multi-step commands.
  - For example, requesting username during login. Any input provided by the user will attempt to be matched to a command.
  - My naive first thought at resolving this is to create context windows which commands are limited during the window.
