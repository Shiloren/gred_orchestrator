from __future__ import annotations

import pytest
from pathlib import Path
from tools.gimo_server.services.skills_service import SkillsService, SkillCreateRequest
from tools.gimo_server.services.skill_bundle_service import SkillBundleService

def _valid_skill_req(name: str, command: str) -> SkillCreateRequest:
    return SkillCreateRequest(
        name=name,
        description="Test skill bundle description",
        command=command,
        replace_graph=False,
        nodes=[{"id": "orch", "type": "orchestrator"}, {"id": "w1", "type": "worker"}],
        edges=[{"source": "orch", "target": "w1"}]
    )

def test_skill_bundle_export_import_cycle(tmp_path, monkeypatch):
    # Setup tmp storage
    monkeypatch.setattr("tools.gimo_server.services.skills_service.SKILLS_DIR", tmp_path / "skills")
    
    # 1. Create a skill
    req = _valid_skill_req("Test Export", "/export-test")
    skill = SkillsService.create_skill(req)
    skill_id = skill.id
    
    # 2. Export to bundle
    bundle_file = tmp_path / "test_skill.zip"
    exported_path = SkillBundleService.export_bundle(skill_id, bundle_file)
    assert exported_path.exists()
    assert exported_path.suffix == ".zip"
    
    # 3. Delete original skill
    assert SkillsService.delete_skill(skill_id) is True
    assert SkillsService.get_skill(skill_id) is None
    
    # 4. Install from bundle
    installed_skill = SkillBundleService.install_bundle(exported_path)
    
    # 5. Verify
    assert installed_skill.name == "Test Export"
    assert installed_skill.command == "/export-test"
    assert len(installed_skill.nodes) == 2
    assert any(n["id"] == "orch" for n in installed_skill.nodes)
    assert len(installed_skill.edges) == 1
    
    # 6. Test overwrite protection
    with pytest.raises(ValueError, match="already exists"):
        SkillBundleService.install_bundle(exported_path, overwrite=False)
        
    # 7. Test overwrite success
    re_installed = SkillBundleService.install_bundle(exported_path, overwrite=True)
    assert re_installed.command == "/export-test"
    assert re_installed.id != installed_skill.id # id is slugified with time

def test_skill_bundle_invalid_bundle(tmp_path):
    # Not a zip
    invalid_zip = tmp_path / "not_a_zip.zip"
    invalid_zip.write_text("corrupt data")
    
    with pytest.raises(Exception):
        SkillBundleService.install_bundle(invalid_zip)
        
    # Missing files in zip
    import zipfile
    missing_files_zip = tmp_path / "missing_files.zip"
    with zipfile.ZipFile(missing_files_zip, 'w') as zf:
        zf.writestr("something.txt", "hello")
        
    with pytest.raises(ValueError, match="missing skill.json"):
        SkillBundleService.install_bundle(missing_files_zip)
