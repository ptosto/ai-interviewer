# Building the AI-interviewer streamlit app.

Run it locally like this:
(base) PS C:\Users\Peter Tosto> cd '.\OneDrive - The Principia\coding\ai-interviewer\ai-interviewer\code\'
(base) PS C:\Users\Peter Tosto\OneDrive - The Principia\coding\ai-interviewer\ai-interviewer\code> conda activate interviews
(interviews) PS C:\Users\Peter Tosto\OneDrive - The Principia\coding\ai-interviewer\ai-interviewer\code> streamlit run interview.py

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://10.130.24.54:8501

Usernames are in secrets.toml

Update the project in github and run it from streamlit community cloud
  https://ai-interviewer-pt.streamlit.app/

Usernames are in Streamlit | Manage App | Settings | Secrets

# ToDo
After making an entry, the chat window needs to scroll so I can see my last response and the new prompt.


# Original repository: https://github.com/friedrichgeiecke/interviews/

# Code for "Conversations at Scale: Robust AI-led Interviews with a Simple Open-Source Platform"

There are two options to explore the AI-led interviews discussed in the paper.

## Option 1: Online notebook

To try own ideas for interviews within minutes and without the need to install Python, see https://colab.research.google.com/drive/1sYl2BMiZACrOMlyASuT-bghCwS5FxHSZ (requires to obtain an API key)

## Option 2: Full platform

To install Python and set up the full interview platform locally (takes around 1h from scratch), see the following steps.

The interview platform is built using the library `streamlit` and the APIs of OpenAI and Anthropic.

- Download miniconda from https://docs.anaconda.com/miniconda/miniconda-install/ and install it (skip if `conda` is already installed)
- Obtain an API key from https://platform.openai.com/ or https://www.anthropic.com/api. In case of the OpenAI API, choose a "project" key
- Download this repository
- In the repository folder on your computer, paste your API key into the file `/code/.streamlit/secrets.toml` (requires to make hidden folders visible)
- In the config.py, select a language model and adjust the interview outline
- In Terminal (Mac) or Anaconda Prompt (Windows), navigate to the folder `code` with `cd` (if unclear, briefly look up basic Linux command line syntax for navigating to folders)
- Once in the `code` folder, create the environment from the .yml file by writing `conda env create -f interviewsenv.yml` and confirming with enter (this installs Python and all libraries necessary to run the platform; only needs to be done once)
- Activate the environment with `conda activate interviews`
- Start the platform with `streamlit run interview.py`


## Paper and citation

The paper is available at https://ssrn.com/abstract=4974382 and can be cited with the following bibtex entry:

```
@article{geieckejaravel2024,
  title={Conversations at Scale: Robust AI-led Interviews with a Simple Open-Source Platform},
  author={Geiecke, Friedrich and Jaravel, Xavier},
  url={https://ssrn.com/abstract=4974382},
  year={2024}
}
```
