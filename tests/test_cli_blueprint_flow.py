"""CLI tests for blueprint-first generation flow."""

from __future__ import annotations

from typer.testing import CliRunner

from workers.cli import app
from workers.io_utils import write_json
from workers.models import ContentCategory, DirectedScript, StoryBlueprint, StoryIdea

runner = CliRunner()


def _make_idea() -> StoryIdea:
    return StoryIdea(
        id="idea_cli_1",
        title="అమ్మ చివరి కాల్",
        category=ContentCategory.EMOTIONAL_SUSPENSE,
        hook="అమ్మ చనిపోయిన తర్వాత ఆమె ఫోన్‌లో ఒక వాయిస్ మెమో కనిపించింది.",
        premise="శ్యామ్ పాత చెరువు గట్టు దగ్గర దొరికిన బొమ్మను చూసి తన పుట్టుక గురించే అనుమానపడటం మొదలుపెడతాడు.",
        twist="ఫోటో వెనక రాసిన వాక్యం వల్ల శ్యామ్ తన తండ్రి గురించి విన్నది మొత్తం అబద్ధమని తెలుస్తుంది.",
        tone="emotional suspense",
    )


def _make_blueprint() -> StoryBlueprint:
    return StoryBlueprint(
        id="blueprint_cli_1",
        idea_id="idea_cli_1",
        title="అమ్మ చివరి కాల్",
        category=ContentCategory.EMOTIONAL_SUSPENSE,
        protagonist_name="శ్యామ్",
        protagonist_role="కొడుకు",
        point_of_view="third_person",
        hook="అమ్మ చనిపోయిన తర్వాత ఆమె ఫోన్‌లో ఒక వాయిస్ మెమో కనిపించింది.",
        central_question="శ్యామ్ జీవితంలో దాచిన నిజం ఏమిటి?",
        primary_story_device="వాయిస్ మెమో",
        primary_clue="పాత ఫోటో",
        supporting_clues=["పిల్లాడు గీసిన బొమ్మ"],
        setup="శ్యామ్ మూడు సంవత్సరాల తర్వాత ఫోన్ తెరిచాడు.",
        escalation="పెట్టెలో దొరికిన జాడలు అతన్ని ఆపలేదు. పాత ఫోటో మళ్లీ అతని ముందుకొచ్చింది.",
        reveal="ఫోటోలో ఉన్న మనిషి అతని తండ్రి కాదు.",
        final_twist="రికార్డింగ్‌లో అమ్మ అతన్ని చెరువు దగ్గర నుంచి తీసుకొచ్చానని అంది. పాత ఫోటో అదే నిజం నిర్ధారించింది.",
        final_line="శ్యామ్ చేతిలో ఇంకా పాత ఫోటోనే ఉంది. అదే అతని జీవితాన్ని మార్చిన చివరి సాక్ష్యం.",
        locations=["పాత ఇల్లు", "చెరువు గట్టు"],
        forbidden_elements=["పాత చీర", "కొత్త పాత్ర"],
    )


def test_script_generation_requires_blueprint(tmp_path, monkeypatch):
    monkeypatch.setattr("workers.config.BLUEPRINTS_DIR", tmp_path / "blueprints")
    monkeypatch.setattr("workers.config.SCRIPTS_DIR", tmp_path / "scripts")
    result = runner.invoke(app, ["generate-script"])
    assert result.exit_code == 1
    assert "Run build-blueprint first" in result.output


def test_failed_blueprint_blocks_generation(tmp_path, monkeypatch):
    blueprints_dir = tmp_path / "blueprints"
    scripts_dir = tmp_path / "scripts"
    blueprints_dir.mkdir()
    scripts_dir.mkdir()
    blueprint = _make_blueprint()
    blueprint.final_twist = ""
    write_json(blueprints_dir / "blueprint_bad.json", blueprint)
    monkeypatch.setattr("workers.config.BLUEPRINTS_DIR", blueprints_dir)
    monkeypatch.setattr("workers.config.SCRIPTS_DIR", scripts_dir)
    result = runner.invoke(app, ["generate-script"])
    assert result.exit_code == 1
    assert "Blueprint failed validation" in result.output


def test_build_blueprint_command_succeeds(tmp_path, monkeypatch):
    ideas_dir = tmp_path / "ideas"
    blueprints_dir = tmp_path / "blueprints"
    ideas_dir.mkdir()
    blueprints_dir.mkdir()
    write_json(ideas_dir / "idea.json", _make_idea())
    monkeypatch.setattr("workers.config.IDEAS_DIR", ideas_dir)
    monkeypatch.setattr("workers.config.BLUEPRINTS_DIR", blueprints_dir)
    result = runner.invoke(app, ["build-blueprint"])
    assert result.exit_code == 0
    assert "Blueprint approved for script generation" in result.output


def test_approved_directed_script_proceeds_to_scene_planning(tmp_path, monkeypatch):
    directed_dir = tmp_path / "scripts" / "directed"
    scenes_dir = tmp_path / "scenes"
    directed_dir.mkdir(parents=True)
    scenes_dir.mkdir()
    write_json(
        directed_dir / "directed_ok.json",
        DirectedScript(
            id="directed_ok",
            source_script_id="script1",
            blueprint_id="blueprint_cli_1",
            title="అమ్మ చివరి కాల్",
            category=ContentCategory.EMOTIONAL_SUSPENSE,
            hook_line="అమ్మ చనిపోయిన తర్వాత ఆమె ఫోన్‌లో ఒక వాయిస్ మెమో కనిపించింది.",
            directed_telugu_script=(
                "అమ్మ చనిపోయిన తర్వాత ఆమె ఫోన్‌లో ఒక వాయిస్ మెమో కనిపించింది.\n\n"
                "శ్యామ్ పాత ఫోటోను చూసి నిజం కనుగొన్నాడు.\n\n"
                "చివరికి అదే ఫోటో అతని తండ్రి గురించి అబద్ధాన్ని బయటపెట్టింది."
            ),
            narrative_score=95,
            quality_score=90,
            telugu_authenticity_score=95,
            continuity_score=92,
            recommendation="approve_candidate",
            approved_for_scene_planning=True,
        ),
    )
    monkeypatch.setattr("workers.config.DIRECTED_SCRIPTS_DIR", directed_dir)
    monkeypatch.setattr("workers.config.SCENES_DIR", scenes_dir)
    monkeypatch.setattr("workers.config.SCRIPTS_DIR", tmp_path / "scripts")
    result = runner.invoke(app, ["plan-scenes", "--allow-unapproved"])
    assert result.exit_code == 0
    assert "Scene plan saved" in result.output
