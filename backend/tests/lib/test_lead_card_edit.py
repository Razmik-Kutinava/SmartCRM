"""Зеркало логики frontend/src/lib/leads/leadCardEdit.js (patch контактов карточки)."""
import pytest

# Дублируем контракт PATCH, который строит leadCardEdit.js на фронте
DASH = "—"


def patch_from_details_draft(draft: dict) -> dict:
	company = draft["company"].strip()
	if not company:
		raise ValueError("Укажите название компании")
	score_raw = draft.get("scoreStr", "").strip()
	score = None
	if score_raw:
		n = int(score_raw)
		if n < 0 or n > 100:
			raise ValueError("Скоринг — целое число от 0 до 100")
		score = n
	patch = {
		"company": company,
		"contact": draft.get("contact", "").strip() or DASH,
		"position": draft.get("position", "").strip() or DASH,
		"email": draft.get("email", "").strip() or DASH,
		"phone": draft.get("phone", "").strip() or DASH,
		"website": draft.get("website", "").strip() or DASH,
		"industry": draft.get("industry", "").strip() or DASH,
		"city": draft.get("city", "").strip() or DASH,
		"employees": draft.get("employees", "").strip() or DASH,
		"budget": draft.get("budget", "").strip() or DASH,
		"next_call": draft.get("nextCall", "").strip() or DASH,
		"description": draft.get("description", "").strip(),
	}
	if score is not None:
		patch["score"] = score
	return patch


def test_patch_details_maps_empty_to_dash():
	p = patch_from_details_draft(
		{"company": "ООО Тест", "contact": "", "email": "", "phone": "", "industry": "", "city": "", "description": ""}
	)
	assert p["company"] == "ООО Тест"
	assert p["contact"] == DASH
	assert p["email"] == DASH


def test_patch_details_score_range():
	with pytest.raises(ValueError):
		patch_from_details_draft({"company": "X", "scoreStr": "101"})


@pytest.mark.asyncio
async def test_api_patch_details_fields(client):
	"""PATCH полей карточки (как UI leadCardEdit) сохраняется."""
	create_r = await client.post("/api/leads", json={"company": "Карточка UI"})
	lead_id = create_r.json()["id"]
	patch = patch_from_details_draft(
		{
			"company": "Карточка UI",
			"contact": "Иван",
			"position": "Директор",
			"email": "ivan@test.local",
			"phone": "+7900",
			"industry": "IT",
			"city": "Москва",
			"description": "заметка",
			"scoreStr": "72",
		}
	)
	r = await client.patch(f"/api/leads/{lead_id}", json=patch)
	assert r.status_code == 200
	data = r.json()
	assert data["contact"] == "Иван"
	assert data["position"] == "Директор"
	assert data["email"] == "ivan@test.local"
	assert data["score"] == 72
	assert data["description"] == "заметка"
