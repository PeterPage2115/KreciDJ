# KreciDJ - Discord Music Bot

KreciDJ is an advanced Discord music bot designed to provide a rich and seamless music experience in your Discord server. Built with `discord.py` and `Wavelink`, it offers a wide range of features, from basic playback to advanced queue management and persistent settings.

## ✨ Key Features

*   **High-Quality Audio:** Powered by Lavalink for stable and high-fidelity audio streaming.
*   **Intelligent Search:** Search for tracks on YouTube and YouTube Music with interactive selection menus.
*   **Direct URL Playback:** Play music directly from YouTube, Spotify, and other supported sources via URL.
*   **Comprehensive Playback Controls:**
    *   `!play <query/url>`: Play a song or add it to the queue.
    *   `!pause` / `!resume`: Pause and resume playback.
    *   `!skip` / `!next`: Skip the current track.
    *   `!stop`: Stop playback and clear the queue.
    *   `!volume <percentage>`: Adjust the bot's volume.
    *   `!seek <HH:MM:SS|MM:SS|SS>`: Jump to a specific timestamp in the current track.
*   **Advanced Queue Management:**
    *   `!queue` / `!q`: Display the current playback queue.
    *   `!clearqueue` / `!cq`: Clear all tracks from the queue.
    *   `!remove <position>`: Remove a specific track from the queue by its number.
    *   `!move <from_pos> <to_pos>`: Move a track from one position to another in the queue.
    *   `!shuffle`: Randomize the order of tracks in the queue.
*   **Looping Functionality:** Toggle between `OFF`, `SINGLE` track loop, and `QUEUE` loop modes.
*   **Interactive Control Panel:** A dynamic "Now Playing" panel with buttons for play/pause, skip, stop, shuffle, loop, volume control, and queue display. The panel automatically updates with track progress and status.
*   **Auto-Disconnect:** The bot automatically disconnects from the voice channel after a period of inactivity to conserve resources.
*   **Persistent Queue:** Music queues are saved to a database and automatically restored when the bot restarts, ensuring your music sessions are never lost.
*   **Customizable Guild Prefixes:** Guild administrators can set a custom command prefix for their server using `!admin setprefix <new_prefix>`.
*   **Robust Error Handling:** Specific and informative error messages for various scenarios (e.g., connection issues, invalid commands, search failures).
*   **Centralized Logging:** Comprehensive logging system for bot events, command usage, and errors.
*   **Health Monitoring:** Built-in health check endpoint for monitoring bot status in containerized environments.
*   **Automated Updates:** Supports automated updates from a Git repository, with "standard" and "nuclear" (full rebuild) modes, and real-time status notifications.

## 🎨 Appearance & Interaction

KreciDJ focuses on a user-friendly experience:

*   **Embed-Rich Responses:** Most bot responses, including search results, queue displays, and status messages, are presented in visually appealing Discord embeds.
*   **Interactive Buttons:** The "Now Playing" panel features intuitive buttons for common playback controls, reducing the need for typing commands.
*   **Search Selection:** When searching for music, the bot presents multiple results with numbered buttons, allowing users to easily select their desired track.
*   **Clear Status Indicators:** The "Now Playing" panel includes a progress bar, volume level, loop status, and queue count, providing a quick overview of the current playback state.

## 🚀 Recent Changes & Improvements

The following significant improvements have been recently implemented:

*   **Enhanced Auto-Disconnect:** Refined activity tracking across all music commands and voice state updates to ensure accurate idle detection and timely disconnections. Includes automatic cleanup of the "Now Playing" panel.
*   **Full Looping Support:** Added `SINGLE` track and `QUEUE` looping modes, accessible via command and the interactive panel.
*   **Granular Error Handling:** Replaced broad `except Exception` blocks with specific exception types for more precise error management and detailed logging.
*   **"Now Playing" Panel Reliability:** Improved the mechanism for updating and managing the "Now Playing" panel, making it more resilient to message deletions and ensuring consistent updates.
*   **Volume Control Integration:** Added dedicated volume up/down buttons to the interactive control panel.
*   **Seek Command:** Introduced the `!seek` command for precise navigation within a playing track.
*   **Advanced Queue Commands:** Implemented `!clearqueue`, `!remove`, and `!move` for comprehensive queue management.
*   **Persistent Queue:** Integrated SQLite database to save and load music queues across bot restarts, ensuring continuity.
*   **Dynamic Command Prefixes:** Enabled per-guild custom command prefixes stored in the database, allowing server owners to personalize the bot's interaction.
*   **Update System Refinements:** Verified and enhanced the Docker-based update scripts (`docker-update.sh`, `manual-update.sh`, `update-monitor.sh`) to ensure robust, automated deployments with detailed Discord notifications upon completion or failure.
*   **Testing Infrastructure:** Set up a basic `tests` directory and added initial unit tests for utility functions, ensuring code quality and stability.

## ⚙️ Installation & Deployment

KreciDJ is designed for Docker-based deployment using `docker-compose`.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-repo/KreciDJ.git
    cd KreciDJ
    ```
2.  **Configure Environment:** Copy `.env.example` to `.env` and fill in your Discord bot token, Lavalink server details, and other configurations.
3.  **Run with Docker Compose:**
    ```bash
    docker-compose up --build -d
    ```
    This will build the bot image, set up the Lavalink server, and start the bot.

## 🤝 Contributing

Contributions are welcome! Please feel free to open issues or submit pull requests.

---

**KreciDJ** - Your ultimate Discord music companion.
**TEST AKTUALIZACJI - Jeśli to widzisz, test się powiódł.**