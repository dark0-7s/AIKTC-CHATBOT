import labelsData from '../../labels.json';

let cachedLabels = null;
export function getLabels() {
  if (!cachedLabels) cachedLabels = labelsData;
  return cachedLabels;
}

export function useLabel(lang, key) {
  const labels = getLabels();
  return labels?.[lang]?.[key] ?? labels?.en?.[key] ?? key;
}
