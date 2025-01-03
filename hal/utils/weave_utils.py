import weave
import time
import requests
import os
import json
from typing import Dict, Any, Tuple, List, Optional
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from .logging_utils import print_step, print_warning, console, create_progress

MODEL_PRICES_DICT = {
                "text-embedding-3-small": {"prompt_tokens": 0.02/1e6, "completion_tokens": 0},
                "text-embedding-3-large": {"prompt_tokens": 0.13/1e6, "completion_tokens": 0},
                "gpt-4o-2024-05-13": {"prompt_tokens": 2.5/1e6, "completion_tokens": 10/1e6},
                "gpt-4o-2024-08-06": {"prompt_tokens": 2.5/1e6, "completion_tokens": 10/1e6},
                "gpt-3.5-turbo-0125": {"prompt_tokens": 0.5/1e6, "completion_tokens": 1.5/1e6},
                "gpt-3.5-turbo": {"prompt_tokens": 0.5/1e6, "completion_tokens": 1.5/1e6},
                "gpt-4-turbo-2024-04-09": {"prompt_tokens": 10/1e6, "completion_tokens": 30/1e6},
                "gpt-4-turbo": {"prompt_tokens": 10/1e6, "completion_tokens": 30/1e6},
                "gpt-4o-mini-2024-07-18": {"prompt_tokens": 0.15/1e6, "completion_tokens": 0.6/1e6},
                "meta-llama/Meta-Llama-3.1-8B-Instruct": {"prompt_tokens": 0.18/1e6, "completion_tokens": 0.18/1e6},
                "meta-llama/Meta-Llama-3.1-70B-Instruct": {"prompt_tokens": 0.88/1e6, "completion_tokens": 0.88/1e6},
                "meta-llama/Meta-Llama-3.1-405B-Instruct": {"prompt_tokens": 5/1e6, "completion_tokens": 15/1e6},
                "Meta-Llama-3-1-70B-Instruct-htzs": {"prompt_tokens": 0.00268/1000, "completion_tokens": 0.00354/1000},
                "Meta-Llama-3-1-8B-Instruct-nwxcg": {"prompt_tokens": 0.0003/1000, "completion_tokens": 0.00061/1000},
                "gpt-4o": {"prompt_tokens": 2.5/1e6, "completion_tokens": 10/1e6},
                "Mistral-small-zgjes": {"prompt_tokens": 0.001/1000, "completion_tokens": 0.003/1000},
                "Mistral-large-ygkys": {"prompt_tokens": 0.004/1000, "completion_tokens": 0.012/1000},
                "o1-mini-2024-09-12": {"prompt_tokens": 3/1e6, "completion_tokens": 12/1e6},
                "o1-preview-2024-09-12": {"prompt_tokens": 15/1e6, "completion_tokens": 60/1e6},
                "claude-3-5-sonnet-20240620": {"prompt_tokens": 3/1e6, "completion_tokens": 15/1e6},
                "claude-3-5-sonnet-20241022": {"prompt_tokens": 3/1e6, "completion_tokens": 15/1e6},
                "us.anthropic.claude-3-5-sonnet-20240620-v1:0": {"prompt_tokens": 3/1e6, "completion_tokens": 15/1e6},
                "us.anthropic.claude-3-5-sonnet-20241022-v2:0": {"prompt_tokens": 3/1e6, "completion_tokens": 15/1e6},
                "openai/gpt-4o-2024-11-20": {"prompt_tokens": 2.5/1e6, "completion_tokens": 10/1e6},
                "openai/gpt-4o-2024-08-06": {"prompt_tokens": 2.5/1e6, "completion_tokens": 10/1e6},
                "openai/gpt-4o-mini-2024-07-18": {"prompt_tokens": 0.15/1e6, "completion_tokens": 0.6/1e6},
                "openai/o1-mini-2024-09-12": {"prompt_tokens": 3/1e6, "completion_tokens": 12/1e6},
                "openai/o1-preview-2024-09-12": {"prompt_tokens": 15/1e6, "completion_tokens": 60/1e6},
                "anthropic/claude-3-5-sonnet-20240620": {"prompt_tokens": 3/1e6, "completion_tokens": 15/1e6},
                "anthropic/claude-3-5-sonnet-20241022": {"prompt_tokens": 3/1e6, "completion_tokens": 15/1e6},
                "google/gemini-1.5-pro": {"prompt_tokens": 1.25/1e6, "completion_tokens": 5/1e6},
                "google/gemini-1.5-flash": {"prompt_tokens": 0.075/1e6, "completion_tokens": 0.3/1e6},
                "together/meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo": {"prompt_tokens": 3.5/1e6, "completion_tokens": 3.5/1e6},
                "together/meta-llama/Meta-Llama-3.1-70B-Instruct": {"prompt_tokens": 0.88/1e6, "completion_tokens": 0.88/1e6},
                "bedrock/amazon.nova-micro-v1:0": {"prompt_tokens": 0.000035/1e3, "completion_tokens": 0.00014/1e3},
                "amazon.nova-micro-v1:0" : {"prompt_tokens": 0.000035/1e3, "completion_tokens": 0.00014/1e3},
                "bedrock/amazon.nova-lite-v1:0": {"prompt_tokens": 0.00006/1e3, "completion_tokens": 0.00024/1e3},
                "amazon.nova-lite-v1:0" : {"prompt_tokens": 0.00006/1e3, "completion_tokens": 0.00024/1e3},
                "bedrock/amazon.nova-pro-v1:0": {"prompt_tokens": 0.0008/1e3, "completion_tokens": 0.0032/1e3},
                "amazon.nova-pro-v1:0" : {"prompt_tokens": 0.0008/1e3, "completion_tokens": 0.0032/1e3},
                "bedrock/us.anthropic.claude-3-5-sonnet-20241022-v2:0": {"prompt_tokens": 0.003/1e3, "completion_tokens": 0.015/1e3},
                "us.anthropic.claude-3-5-sonnet-20241022-v2:0" : {"prompt_tokens": 0.003/1e3, "completion_tokens": 0.015/1e3},
                "bedrock/us.anthropic.claude-3-sonnet-20240229-v1:0": {"prompt_tokens": 0.003/1e3, "completion_tokens": 0.015/1e3},
                "us.anthropic.anthropic.claude-3-sonnet-20240229-v1:0" : {"prompt_tokens": 0.003/1e3, "completion_tokens": 0.015/1e3},
                "bedrock/us.anthropic.claude-3-5-haiku-20241022-v1:0": {"prompt_tokens": 0.0008/1e3, "completion_tokens": 0.004/1e3},
                "us.anthropic.claude-3-5-haiku-20241022-v1:0" : {"prompt_tokens": 0.0008/1e3, "completion_tokens": 0.004/1e3}, 
                "bedrock/us.meta.llama3-3-70b-instruct-v1:0": {"prompt_tokens": 0.00072/1e3, "completion_tokens": 0.00072/1e3},
                "us.meta.llama3-3-70b-instruct-v1:0" : {"prompt_tokens": 0.00072/1e3, "completion_tokens": 0.00072/1e3}, 
}

def fetch_weave_calls(client) -> List[Dict[str, Any]]:
    """Fetch Weave calls from the API"""
    url = 'https://trace.wandb.ai/calls/stream_query'
    headers = {'Content-Type': 'application/json'}
    payload = {"project_id": client._project_id()}

    response = requests.post(
        url, 
        headers=headers, 
        json=payload, 
        auth=('api', os.getenv('WANDB_API_KEY'))
    )
    return [json.loads(line) for line in response.text.strip().splitlines()]

def process_usage_data(calls: List[Dict[str, Any]], progress: Progress) -> Tuple[float, Dict[str, Dict[str, int]]]:
    """Process usage data from Weave calls"""
    usage_calls = []
    unique_model_names = set()
    
    task = progress.add_task("Processing usage data...", total=len(calls))
    
    for call in calls:
        try:
            if 'summary' in call and 'usage' in call['summary']:
                usage_calls.append(call['summary']['usage'])
        except (KeyError, TypeError) as e:
            print_warning(f"Error processing call: {str(e)}")
        progress.update(task, advance=1)
    
    return calculate_costs(usage_calls)

def calculate_costs(usage_calls: List[Dict[str, Any]]) -> Tuple[float, Dict[str, Dict[str, int]]]:
    """Calculate total costs and token usage from processed calls"""
    unique_model_names = set(model_name for call in usage_calls for model_name in call)
    
    # Validate models
    for model_name in unique_model_names:
        if model_name not in MODEL_PRICES_DICT:
            raise KeyError(f"Model '{model_name}' not found in MODEL_PRICES_DICT.")
    
    total_cost = 0
    token_usage = {model: {"prompt_tokens": 0, "completion_tokens": 0} for model in unique_model_names}
    
    for call in usage_calls:
        for model_name in call:
            if 'prompt_tokens' in call[model_name] and 'completion_tokens' in call[model_name]:
                # Standard call
                token_usage[model_name]["prompt_tokens"] += call[model_name]["prompt_tokens"]
                token_usage[model_name]["completion_tokens"] += call[model_name]["completion_tokens"]
                total_cost += (
                    MODEL_PRICES_DICT[model_name]["prompt_tokens"] * call[model_name]["prompt_tokens"] +
                    MODEL_PRICES_DICT[model_name]["completion_tokens"] * call[model_name]["completion_tokens"]
                )
            elif 'input_tokens' in call[model_name] and 'output_tokens' in call[model_name]:
                # Tool use call
                token_usage[model_name]["prompt_tokens"] += call[model_name]["input_tokens"]
                token_usage[model_name]["completion_tokens"] += call[model_name]["output_tokens"]
                total_cost += (
                    MODEL_PRICES_DICT[model_name]["prompt_tokens"] * call[model_name]["input_tokens"] +
                    MODEL_PRICES_DICT[model_name]["completion_tokens"] * call[model_name]["output_tokens"]
                )
    
    return total_cost, token_usage

def get_total_cost(client) -> Tuple[Optional[float], Dict[str, Dict[str, int]]]:
    """Get total cost and token usage for all Weave calls"""
    print_step("Calculating total cost...")
    
    with create_progress() as progress:
        # Fetch calls
        task1 = progress.add_task("Fetching Weave calls...", total=1)
        calls = fetch_weave_calls(client)
        progress.update(task1, completed=1)
        
        try:
            # Process calls and calculate costs
            total_cost, token_usage = process_usage_data(calls, progress)
            console.print(f"[green]Total cost: ${total_cost:.6f}[/]")
            return total_cost, token_usage
            
        except KeyError as e:
            print_warning(f"Error calculating costs: {str(e)}")
            return None, {
                model_name: {"prompt_tokens": None, "completion_tokens": None}
                for model_name in set(model_name for call in calls for model_name in call.get('summary', {}).get('usage', {}))
            }
            
def comput_cost_from_inspect_usage(usage: Dict[str, Dict[str, int]]) -> float:
    """Compute cost from token usage"""
    return sum(MODEL_PRICES_DICT[model_name]["prompt_tokens"] * usage[model_name]["input_tokens"] +
               MODEL_PRICES_DICT[model_name]["completion_tokens"] * usage[model_name]["output_tokens"] for model_name in usage)

def process_weave_output(call: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single Weave call output"""
    if call['output']:
        if isinstance(call['output'], str):
            ChatCompletion = weave.ref(call['output']).get()
            try:
                choices = [choice.message.content for choice in ChatCompletion.choices]
                created = ChatCompletion.created
            except AttributeError:
                choices = [content.text for content in ChatCompletion.content]
                created = call['started_at']
        elif 'choices' in call['output']:
            choices = call['output']['choices']
            created = call['output']['created']
        elif call['output']['content']: # tooluse
                choices = call['output']['content']
                created = None
        
        return {
            'weave_task_id': call['attributes']['weave_task_id'],
            'trace_id': call['trace_id'],
            'project_id': call['project_id'],
            'created_timestamp': created,
            'inputs': call['inputs'],
            'id': call['id'],
            'outputs': choices,
            'exception': call['exception'],
            'summary': call['summary'],
            'display_name': call['display_name'],
            'attributes': call['attributes'],
        }
    return {}

def get_weave_calls(client) -> List[Dict[str, Any]]:
    """Get processed Weave calls with progress tracking"""
    print_step("Retrieving Weave traces...")
    
    with create_progress() as progress:
        # Fetch calls
        task1 = progress.add_task("Fetching Weave calls...", total=1)
        calls = fetch_weave_calls(client)
        progress.update(task1, completed=1)
        
        # Process calls
        processed_calls = []
        task2 = progress.add_task("Processing calls... (this can take a while)", total=len(calls))
        
        for call in calls:
            processed_call = process_weave_output(call)
            if processed_call:
                processed_calls.append(processed_call)
            progress.update(task2, advance=1)
    
    console.print(f"[green]Total Weave traces: {len(processed_calls)}[/]")
    return processed_calls

def assert_task_id_logging(client, weave_task_id: str) -> bool:
    """Assert that task ID is properly logged in Weave calls"""
    with create_progress() as progress:
        task = progress.add_task("Checking task ID logging...", total=1)
        calls = fetch_weave_calls(client)
        
        for call in calls:
            if str(call['attributes'].get('weave_task_id')) == str(weave_task_id):
                progress.update(task, completed=1)
                return True
                
        progress.update(task, completed=1)
        raise AssertionError(
            "Task ID not logged or incorrect ID for test run. "
            "Please use weave.attributes to log the weave_task_id for each API call."
        )