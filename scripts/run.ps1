param(
  [string]$Config = "config.yaml"
)

python -m src.app --config $Config
