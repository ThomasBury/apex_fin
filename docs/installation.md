# Installation

This guide provides instructions on how to set up and configure the `apex-fin` project using `uv` for dependency management.

## 🛠️ Setup

1. **Clone the repository:**

    ```bash
    git clone https://github.com/your-org/apex_fin.git
    cd apex_fin
    ```

    Replace `https://github.com/your-org/apex_fin.git` with the actual repository URL if it's different.

2. **Install dependencies:**
    Use `uv` to synchronize the project's dependencies based on the `pyproject.toml` file.

    ```bash
    uv sync
    ```

3. **Configuration:**
   Detailed configuration options for `apex-fin`, including environment variables and the `apex_fin.yaml` file, are covered in the [Detailed Configuration](./configuration.md) guide.

   For information on customizing the prompts used by the LLM agents, refer to the [Customizing Prompts](./prompts_customization.md) documentation.
