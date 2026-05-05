# Backend

## Getting started

The repository uses submodules. The first step is to initialise all submodules recursively.

```bash
git submodule init
git submodule update --recursive
```

Because the project is split into multiple parts, it's necessary to create multiple virtual environments. Whenever you work within one of these folders—`backend`, `synthetic-users`, `frontend`, or `process_experiment_log`—ensure you switch to the corresponding virtual environment before running any commands.

1. Clone the repository.
2. Create and activate a Python virtual environment.
3. Install dependencies from `requirements.txt` file.

```bash
# create a backend virtual environment
(
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
)
# create a synthetic-users virtual environment
(
cd synthetic-users
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
)
```

The `process_experiment_log` uses a Jupyter notebook. Open it using your chosen conda environment, or create a `.venv` environment. The `requirements.txt` file lists all packages required for base Python to run the notebook.

```bash
# from artefact/dissertation
(
cd process_experiment_log
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
)
```

## Server

Create a `JWT_SECRET_KEY` for signing tokens using openssl:

```bash
openssl rand -base64 64
```

Before running the backend, create a .env file to set environment variables and remove any line breaks in the key after you paste it into the file.

```.env
SQLALCHEMY_DATABASE_URI=sqlite:///database.db
JWT_SECRET_KEY=<openssl_secret>
UNITY_ROOT=unity_build
```

### Running the server

Remember to switch to the correct environment before running any Python code.

```bash
cd backend
source .venv/bin/activate
```

Initialise the database:

```bash
python -m cli.recreate_db
```

Finally, run the Flask backend:

```bash
flask run
```

## Experiments

### Synthesise users

To synthesize users the **server must be running**. Additionally, don't forget to switch to the correct virtual environment.

```bash
( 
cd synthetic-users
source .venv/bin/activate
python main.py
)
```

To adjust the number of students and the number of questions per student, adjust the constants at the top of the `synthetic-users/main.py` file.

### Training on synthesised students

To run and train the knowledge tracing models on the synthesised student data. First, the data must be exported from the database to a CSV file. To do this, switch to the backend virtual environment and execute the db_to_csv script:

```bash
(
cd backend/
source .venv/bin/activate
python -m cli.db_to_csv
)
```

This creates a folder for each LLM in the `backend/pykt-toolkit/data` folder.

Next, you must preprocess the data:

```bash
(
cd backend/pykt-toolkit/examples
python data_preprocess.py --dataset_name="smart_tutor_llama3.2:latest"
python data_preprocess.py --dataset_name="smart_tutor_mistral:latest"
python data_preprocess.py --dataset_name="smart_tutor_gemma3:1b"
python data_preprocess.py --dataset_name="smart_tutor_qwen2.5:latest"
python data_preprocess.py --dataset_name="smart_tutor_deepseek-r1:1.5b" 
)
```

And finally, to train the models, execute the script:

```bash
(
cd backend/pykt-toolkit/examples
./run_experiment.sh
)
```

To add datasets or knowledge tracing models, adjust the models at the top of the file. Note that the datasets must be in the lookup table in `data_preprocess.py`, and the data itself must be in the directory specified by the same lookup table. The models must be existing models in the `backend/pykt-toolkit/examples` directory in the `wandb_<model_name>_train.py` format.

```bash
cp backend/pykt-toolkit/experiment_log.csv process_experiment_log/experiment_log.csv
```

This creates a login `backend/pykt-toolkit` to run and generate LaTeX tables using this data. The log is copied to `dissertation/process_experiment_log/`, and the `notebook.ipynb` is used in the same directory.

All the model checkpoints are written to `backend/pykt-toolkit/example/experiment_models`. The shell script automatically skips any model checkpoints that have already been created. This is to avoid accidentally overwriting models and losing hours of training. To retrain a model, its checkpoint must be moved or deleted.

### Data Analysis

Some data analysis was done by querying the database directly through SQL. These queries are in `backend/instance/query.sql`.

```bash
sqlite3 backend/instance/database.db < backend/instance/query.sql
```
