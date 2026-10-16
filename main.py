from fastapi.middleware.cors import CORSMiddleware
from dotenv import dotenv_values
import os
from pathlib import Path
import yaml
from fastapi import FastAPI, Request

BASE_DIR = Path(__file__).parent
PREFIX = "APP_"
DOTENV_ALIASES = {"NUM_WORKERS": "workers"}
INT_KEYS = {"port", "workers"}
BOOL_KEYS = {"debug"}
TRUTHY = {"true", "1", "yes", "on"}

DEFAULTS = {
	"port": 8000,
	"workers": 1,
	"debug": False,
	"log_level": "info",
	"api_key": "default-secred-000",
}

app = FastAPI()
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_methods=["*"],
	allow_headers=["*"],
)

@app.get("/effective-config")
def effective_config(request: Request):
	env = os.getenv("APP_ENV", "development") 

	merged = dict(DEFAULTS)

	yaml_layer = load_yaml_layer(env)
	merged.update(yaml_layer)
	merged.update(load_dotenv_layer())
	merged.update(load_os_layer())

	requests = request.query_params.getlist("set")
	for i in requests:
		key, sep, value = i.partition("=")
		key = key.strip().lower()
		if sep and key:
			merged[key] = value

	result = {k: coerce(k, v) for k, v in merged.items()}
	result["api_key"] = "****"
	return result
	return merged

def load_dotenv_layer():
	raw = dotenv_values(BASE_DIR / ".env")
	out = {}
	for name, value in raw.items():
		if value is None:
			continue
		if name in DOTENV_ALIASES:
			out[DOTENV_ALIASES[name]] = value
		elif name.startswith(PREFIX):
			out[name[len(PREFIX):].lower()] = value
	return out

def load_yaml_layer(env):
	path = BASE_DIR / f"config.{env}.yaml"
	if not path.exists():
		return {}
	with open(path) as f:
		data = yaml.safe_load(f) or {}
	return data

def load_os_layer():
	out = {}
	for name, value in os.environ.items():
		if name == "APP_ENV":
			continue
		if name.startswith(PREFIX):
			out[name[len(PREFIX):].lower()] = value
	return out

def coerce(key, value):
	if key in INT_KEYS:
		return int(value)
	if key in BOOL_KEYS:
		if isinstance(value, bool):
			return value
		return str(value).strip().lower() in TRUTHY
	return str(value)
