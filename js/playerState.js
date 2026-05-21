/**
 * playerState.js — минимальный API для чтения/записи состояния игрока.
 * Ключ хранения: awara_v258_state (новый), миграция с awara_v255_state.
 * Никакой игровой логики — только I/O.
 */

const STORAGE_KEY = 'awara_v258_state';
const LEGACY_KEY  = 'awara_v255_state';

const DEFAULT_STATE = {
  totalLight: 0,
  sphereData: {},
  spirit: {
    'Любовь': 10,
    'Мудрость': 10,
    'Воля': 10,
    'Радость': 10,
    'Истина': 10
  },
  elements: {
    'Огонь': 0,
    'Вода': 0,
    'Земля': 0,
    'Воздух': 0,
    'Эфир': 0
  },
  cauldron: {
    entriesCount: 0,
    lastEntryAt: null,
    lastResult: null
  },
  activeSystem: 'Ведическая',
  journey: [],
  soulPassport: {
    ray: null,
    guna: null,
    path: null,
    archetypeSummary: null
  }
};

/**
 * Миграция из legacy-ключа awara_v255_state в awara_v258_state.
 * Если новый ключ уже существует — миграция не нужна.
 * Возвращает мигрированные данные или null.
 */
export function migrate() {
  if (localStorage.getItem(STORAGE_KEY)) return null;

  const raw = localStorage.getItem(LEGACY_KEY);
  if (!raw) return null;

  try {
    const legacy = JSON.parse(raw);
    const migrated = {
      totalLight:   legacy.totalLight   ?? DEFAULT_STATE.totalLight,
      sphereData:   legacy.sphereData   ?? DEFAULT_STATE.sphereData,
      spirit:       legacy.spirit       ?? { ...DEFAULT_STATE.spirit },
      elements:     legacy.elements     ?? { ...DEFAULT_STATE.elements },
      cauldron:     legacy.cauldron     ?? { ...DEFAULT_STATE.cauldron },
      activeSystem: legacy.activeSystem ?? DEFAULT_STATE.activeSystem,
      journey:      legacy.journey      ?? [],
      soulPassport: legacy.soulPassport ?? { ...DEFAULT_STATE.soulPassport }
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(migrated));
    return migrated;
  } catch (e) {
    console.warn('playerState: ошибка миграции из ' + LEGACY_KEY, e);
    return null;
  }
}

/**
 * Чтение состояния. Пробует новый ключ, затем миграцию,
 * затем возвращает дефолт.
 */
export function getState() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (raw) {
    try {
      const data = JSON.parse(raw);
      return {
        totalLight:   data.totalLight   ?? DEFAULT_STATE.totalLight,
        sphereData:   data.sphereData   ?? DEFAULT_STATE.sphereData,
        spirit:       data.spirit       ?? { ...DEFAULT_STATE.spirit },
        elements:     data.elements     ?? { ...DEFAULT_STATE.elements },
        cauldron:     data.cauldron     ?? { ...DEFAULT_STATE.cauldron },
        activeSystem: data.activeSystem ?? DEFAULT_STATE.activeSystem,
        journey:      data.journey      ?? [],
        soulPassport: data.soulPassport ?? { ...DEFAULT_STATE.soulPassport }
      };
    } catch (e) {
      console.warn('playerState: ошибка чтения ' + STORAGE_KEY, e);
    }
  }

  const migrated = migrate();
  if (migrated) return migrated;

  return { ...DEFAULT_STATE, spirit: { ...DEFAULT_STATE.spirit }, elements: { ...DEFAULT_STATE.elements }, cauldron: { ...DEFAULT_STATE.cauldron }, journey: [], soulPassport: { ...DEFAULT_STATE.soulPassport } };
}

/**
 * Сохранение состояния в localStorage.
 * Принимает объект с полями totalLight, sphereData, spirit, elements,
 * activeSystem, journey, soulPassport.
 */
export function saveState(state) {
  const data = {
    totalLight:   state.totalLight   ?? 0,
    sphereData:   state.sphereData   ?? {},
    spirit:       state.spirit       ?? {},
    elements:     state.elements     ?? {},
    cauldron:     state.cauldron     ?? { ...DEFAULT_STATE.cauldron },
    activeSystem: state.activeSystem ?? 'Ведическая',
    journey:      state.journey      ?? [],
    soulPassport: state.soulPassport ?? { ...DEFAULT_STATE.soulPassport }
  };
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch (e) {
    console.warn('playerState: ошибка записи', e);
  }
}
