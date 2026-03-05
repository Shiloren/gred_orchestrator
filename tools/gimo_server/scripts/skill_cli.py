from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Add the project root to sys.path to allow imports if run as a script
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from tools.gimo_server.services.skill_bundle_service import SkillBundleService
from tools.gimo_server.services.skills_service import SkillExecuteRequest, SkillsService


async def handle_export(args: argparse.Namespace):
    out_path = Path(args.out) if args.out else Path.cwd() / f"{args.skill_id}.zip"
    try:
        exported = SkillBundleService.export_bundle(args.skill_id, out_path)
        print(f"Skill exported successfully to: {exported}")
    except Exception as e:
        print(f"Error exporting skill: {e}", file=sys.stderr)
        sys.exit(1)


async def handle_install(args: argparse.Namespace):
    try:
        skill = SkillBundleService.install_bundle(Path(args.bundle), overwrite=args.overwrite)
        print(f"Skill installed successfully: {skill.name} ({skill.id})")
    except Exception as e:
        print(f"Error installing skill: {e}", file=sys.stderr)
        sys.exit(1)


async def handle_run(args: argparse.Namespace):
    try:
        # Try to find skill by ID or command
        skill = SkillsService.get_skill(args.skill_id)
        if not skill:
            all_skills = SkillsService.list_skills()
            skill = next((s for s in all_skills if s.command == args.skill_id), None)

        if not skill:
            print(
                f"Error: Skill '{args.skill_id}' not found (as ID or command).", file=sys.stderr
            )
            sys.exit(1)

        req = SkillExecuteRequest(replace_graph=args.replace_graph)
        resp = await SkillsService.execute_skill(skill.id, req)
        print(f"Skill execution triggered for: {skill.name} ({skill.command})")
        print(f"Run ID: {resp.skill_run_id} (status: {resp.status})")
        # Give a moment for background task
        await asyncio.sleep(0.5)
    except Exception as e:
        print(f"Error running skill: {e}", file=sys.stderr)
        sys.exit(1)


async def main():
    parser = argparse.ArgumentParser(description="GIMO Skill CLI - AI Containers Base")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Export
    export_parser = subparsers.add_parser("export", help="Export a skill to a bundle")
    export_parser.add_argument("skill_id", help="ID of the skill to export")
    export_parser.add_argument("--out", help="Output directory or file path")

    # Install
    install_parser = subparsers.add_parser("install", help="Install a skill from a bundle")
    install_parser.add_argument("bundle", help="Path to the .zip bundle")
    install_parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing skill with same command"
    )

    # Run
    run_parser = subparsers.add_parser("run", help="Execute a skill")
    run_parser.add_argument(f"skill_id", help="ID or command of the skill to run")
    run_parser.add_argument(
        "--replace-graph", action="store_true", help="Run with replace_graph=True"
    )

    args = parser.parse_args()

    if args.command == "export":
        await handle_export(args)
    elif args.command == "install":
        await handle_install(args)
    elif args.command == "run":
        await handle_run(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
