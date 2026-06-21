/** Паспорт клиента — данные из lead.checko + поля лида. */

export const PASSPORT_SECTIONS = [
	{ id: 'general', label: 'Общая информация' },
	{ id: 'reliability', label: 'Надёжность' },
	{ id: 'requisites', label: 'Реквизиты' },
	{ id: 'contacts', label: 'Контакты' },
	{ id: 'activities', label: 'Виды деятельности' },
	{ id: 'financials', label: 'Финансовая отчётность' },
	{ id: 'taxes', label: 'Налоги и сборы' },
	{ id: 'director', label: 'Руководитель' },
	{ id: 'founders', label: 'Учредитель' },
	{ id: 'branches', label: 'Филиалы' },
	{ id: 'connections', label: 'Связи' },
	{ id: 'licenses', label: 'Лицензии' },
	{ id: 'fedresurs', label: 'Федресурс' },
	{ id: 'contracts', label: 'Госзакупки' },
	{ id: 'inspections', label: 'Проверки и КНМ' },
	{ id: 'arbitration', label: 'Арбитражные дела' },
	{ id: 'debts', label: 'Долги' },
	{ id: 'vacancies', label: 'Вакансии' },
	{ id: 'history', label: 'История изменений' },
	{ id: 'tech', label: 'Технологии' },
];

const STATUS_RU = {
	ACTIVE: 'Действует',
	LIQUIDATING: 'Ликвидируется',
	LIQUIDATED: 'Ликвидирован',
	BANKRUPT: 'Банкротство',
	REORGANIZING: 'Реорганизация',
};

export function passportSource(lead) {
	const ck = lead?.checko || {};
	const co = ck.company || {};
	const fin = { ...(lead?.financials || {}), ...(ck.financials || {}) };
	const tech = { ...(lead?.tech || {}), ...(ck.tech || {}) };
	return { ck, co, fin, tech };
}

export function formatPassportMoney(v) {
	if (v == null || v === '') return null;
	const n = Number(v);
	if (Number.isNaN(n)) return String(v);
	if (n >= 1e9) return `${(n / 1e9).toFixed(1)} млрд ₽`;
	if (n >= 1e6) return `${(n / 1e6).toFixed(1)} млн ₽`;
	return `${n.toLocaleString('ru')} ₽`;
}

export function formatPassportStatus(status) {
	if (!status) return null;
	return STATUS_RU[status] || String(status);
}

export function passportReliability(co, fin) {
	const risks = co.risk_flags || {};
	let score = 100;
	const flags = [];
	if (risks.is_bad_supplier) {
		score -= 35;
		flags.push('Недобросовестный поставщик');
	}
	if (risks.has_disqualified_leader) {
		score -= 25;
		flags.push('Дисквалифицированный руководитель');
	}
	if (risks.is_mass_address) {
		score -= 10;
		flags.push('Массовый адрес');
	}
	if (fin.has_bankruptcy) {
		score -= 40;
		flags.push('Сообщения о банкротстве');
	}
	if ((fin.enforcement_count || 0) > 0) {
		score -= 15;
		flags.push(`Исполнительные производства: ${fin.enforcement_count}`);
	}
	if ((fin.arbitration_count || 0) > 10) {
		score -= 10;
		flags.push(`Арбитражных дел: ${fin.arbitration_count}`);
	}
	score = Math.max(0, Math.min(100, score));
	const tier = score >= 70 ? 'Высокий' : score >= 40 ? 'Средний' : 'Низкий';
	return { score, tier, flags };
}

export function passportActivityTypes(co, lead) {
	const items = [];
	const main = co.okved || lead?.industry;
	const mainName = co.okved_name || '';
	if (main || mainName) {
		items.push({
			code: main || '—',
			name: mainName || '—',
			primary: true,
		});
	}
	for (const extra of co.okved_extra || co.okved_list || []) {
		if (typeof extra === 'string') {
			items.push({ code: extra, name: '', primary: false });
		} else if (extra && typeof extra === 'object') {
			items.push({
				code: extra.code || extra.Код || '—',
				name: extra.name || extra.Наим || '',
				primary: false,
			});
		}
	}
	return items;
}

export function passportBranches(co) {
	if (Array.isArray(co.branches) && co.branches.length) {
		return co.branches.map((b) => ({
			name: b.name || b.Наим || '—',
			address: b.address || b.Адрес || '',
			kpp: b.kpp || b.КПП || '',
		}));
	}
	const n = co.branch_count;
	if (n != null && n > 0) {
		return [{ name: `Филиалов в ЕГРЮЛ: ${n}`, address: '', kpp: '' }];
	}
	return [];
}

export function passportConnections(co) {
	const out = [];
	for (const rc of co.related_companies || []) {
		out.push({
			name: rc.name_full || rc.name || '—',
			inn: rc.inn || '',
			ogrn: rc.ogrn || '',
			status: formatPassportStatus(rc.status) || rc.status || '',
			okved: rc.okved || '',
			address: rc.address || '',
			relation: rc._relation || 'Связанная компания',
		});
	}
	return out;
}

export function passportLicenses(co, fin) {
	const fromCo = co.licenses || [];
	const fromFin = fin.licenses || [];
	return [...new Set([...fromCo, ...fromFin].filter(Boolean))];
}

export function passportDirector(lead, co) {
	const name = co.director || lead?.contact;
	const post = co.director_post || lead?.position;
	if (!name || name === '—') return null;
	return { name, post: post && post !== '—' ? post : '' };
}

export function passportTaxes(fin) {
	const rows = [];
	if (fin.tax_debt != null) {
		rows.push(['Задолженность по налогам', formatPassportMoney(fin.tax_debt)]);
	}
	if (fin.tax_paid != null) {
		rows.push(['Уплачено налогов', formatPassportMoney(fin.tax_paid)]);
	}
	return rows;
}

export function passportDebts(fin) {
	const items = [];
	if (fin.debt != null) {
		items.push({ label: 'Кредиторская задолженность (баланс)', amount: fin.debt });
	}
	if (fin.enforcement_debt) {
		items.push({ label: 'ФССП (сумма по открытым ИП)', amount: fin.enforcement_debt });
	}
	if (fin.tax_debt != null) {
		items.push({ label: 'Налоговая задолженность', amount: fin.tax_debt });
	}
	for (const e of fin.enforcements || []) {
		items.push({
			label: e.reason || e.number || 'Исполнительное производство',
			amount: e.amount,
			date: e.date,
		});
	}
	return items;
}

export function passportHasData(lead) {
	if (!lead) return false;
	if (lead.inn) return true;
	const { ck } = passportSource(lead);
	return Object.keys(ck).length > 0;
}

export function passportSectionCount(sectionId, lead) {
	const { co, fin, tech } = passportSource(lead);
	switch (sectionId) {
		case 'contacts':
			return (co.phones?.length || 0) + (co.emails?.length || 0) + (lead?.website && lead.website !== '—' ? 1 : 0);
		case 'activities':
			return passportActivityTypes(co, lead).length;
		case 'founders':
			return co.founders?.length || 0;
		case 'connections':
			return passportConnections(co).length;
		case 'licenses':
			return passportLicenses(co, fin).length;
		case 'fedresurs':
			return fin.fedresurs_count || fin.fedresurs_messages?.length || 0;
		case 'contracts':
			return fin.contracts_count || fin.contracts?.length || 0;
		case 'inspections':
			return fin.inspection_count || fin.inspections?.length || 0;
		case 'arbitration':
			return fin.arbitration_count || fin.arbitration_cases?.length || 0;
		case 'debts':
			return passportDebts(fin).length;
		case 'tech':
			return tech.count || tech.all?.length || 0;
		default:
			return 0;
	}
}
