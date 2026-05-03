## Getting started

The repository uses modules. So the first step is to initialize all the submodules recursively.

```bash
git submodule init
git submodule sync --recursive
git submodule update --recursive
```

Because the project is split into multiple parts it's nessesary to create multiple virtual environments. The folders that expect to have a virtual environment and to have all dependencies downloaded are `backend`, `synthetic-users`, `frontend`, although the `frontend` is an old python demo UI and has been depricated. `unity-frontend` should be used instead.

1. Clone the repository.
2. Create and activate a Python virtual environment.
3. Install dependencies from `requirements.txt` file.
4. Configure any dataset paths, API keys, or local model settings as needed.
5. Run the smart tutor app or experiment scripts from the appropriate subdirectory.

Example setup:

```bash
git clone https://github.com/jakubwj2/dissertation.git
# create backend virtual environtment
cd dissertation/backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
# create synthetic-users virtual environtment
cd ../synthetic-users
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
# create frontend virtual environtment
cd ../frontend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Backend
Before running the backend, you must create a .env file to set environment variables
```.env
SQLALCHEMY_DATABASE_URI=sqlite:///database.db
JWT_SECRET_KEY=some_secret
UNITY_ROOT=unity_build
``` 
you must also create the databe

```bash
python -m cli.recreate_db
```

To run the backend run flask
```bash
flask run
```
## Experiments

The experimental workflow is designed around comparing KT algorithms on synthetic learner interaction data produced by LLMs, then checking whether those conclusions remain consistent when compared with real-world data such as ASSISTments.

This may include:

- generating synthetic student sequences;
- training KT models under controlled settings;
- evaluating predictive metrics such as accuracy and AUC;
- comparing results across synthesizers, models, and datasets.

## Smart tutor

The smart tutor component provides the application context for the dissertation. It targets simple maths operations and uses a hybrid question system with bespoke IDs to balance runtime generation and persistent question storage.

This allows the project to connect learner interaction generation, tutoring behaviour, and downstream KT evaluation in a single workflow.
