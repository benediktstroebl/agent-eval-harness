from setuptools import setup, find_packages

setup(
    name="agent_eval_harness",
    version="0.1.0",
    description="",
    python_requires=">=3.9",
    packages=find_packages(include=["agent_eval_harness*"]),
    install_requires=[
        'datasets',
        'weave',
        'pydantic>=2.0.0',
        'huggingface-hub',
        'python-dotenv',
    ],
)