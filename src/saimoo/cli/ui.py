import click
import os
import subprocess

@click.command()
@click.option('--port', default=8501, help='Streamlit server port')
def ui(port):
    """Launch the Saimoo Web UI"""
    # Get path to the streamlit app file
    # src/saimoo/web/app.py
    import saimoo.web.app as web_app
    app_path = os.path.abspath(web_app.__file__)
    
    cmd = ["uv", "run", "streamlit", "run", app_path, "--server.port", str(port)]
    
    click.echo(f"Starting Saimoo UI on port {port}...")
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        click.echo("Stopping UI...")
