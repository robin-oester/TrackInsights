import { DisciplineType, DropdownData, DropdownItem, SelectionType } from "../types/bestlistTypes.ts";


export const API_BASE_URL = 'http://localhost:5050/api';

export const AVAILABLE_CATEGORIES: DropdownData = {
  default: "all_m",
  items: [
    {key: "all_m", value_en: "All Men", value_de: "Alle Männer", id: "all_m"},
    {key: "all_f", value_en: "All Women", value_de: "Alle Frauen", id: "all_f"},
    {key: "men", value_en: "Men", value_de: "Männer", id: "m"},
    {key: "women", value_en: "Women", value_de: "Frauen", id: "f"},
    {key: "u23_m", value_en: "U23 M", id: "u23_m"},
    {key: "u23_f", value_en: "U23 W", id: "u23_f"},
    {key: "u20_m", value_en: "U20 M", id: "u20_m"},
    {key: "u20_f", value_en: "U20 W", id: "u20_f"},
    {key: "u18_m", value_en: "U18 M", id: "u18_m"},
    {key: "u18_f", value_en: "U18 W", id: "u18_f"},
    {key: "u16_m", value_en: "U16 M", id: "u16_m"},
    {key: "u16_f", value_en: "U16 W", id: "u16_f"},
    {key: "u14_m", value_en: "U14 M", id: "u14_m"},
    {key: "u14_f", value_en: "U14 W", id: "u14_f"},
    {key: "u12_m", value_en: "U12 M", id: "u12_m"},
    {key: "u12_f", value_en: "U12 W", id: "u12_f"},
    {key: "u10_m", value_en: "U10 M", id: "u10_m"},
    {key: "u10_f", value_en: "U10 W", id: "u10_f"}
  ]
};
export const AVAILABLE_YEARS: DropdownData = generateYearsData();
export const AVAILABLE_SEASONS: DropdownData = generateSeasonData();
export const AVAILABLE_LIMITS: DropdownData= generateLimitsData([10, 30, 100, 500, 5000]);
export const AVAILABLE_RANGE_TYPES: DropdownData = {
  items: [
    {key: "score", value_en: "Score", value_de: "Punkte", id: "score"}
  ]
};

export function getSelectionId(keys: Set<string>, data: DropdownData): SelectionType {
  if (keys.size === 0) {
    return undefined;
  }
  const selectedKey = Array.from(keys)[0]
  const item = data.items.find((val) => val.key === selectedKey)
  if (!item || item.id === null) {
    return undefined;
  }
  return item.id;
}

export function getInitialValue(data: DropdownData): Set<string> {
  const defaultValue = data.default;
  return defaultValue === undefined ? new Set([]) : new Set([defaultValue]);
}

function generateYearsData(startYear: number = 2006): DropdownData {
  const currentYear = new Date().getFullYear();
  const years: DropdownItem[] = [];

  years.push({key: "all", value_en: "All", value_de: "Alle", id: null});
  for (let year = currentYear; year >= startYear; year--) {
    years.push({key: year.toString(), value_en: year.toString(), id: year});
  }

  return {default: currentYear.toString(), items: years};
}

function generateSeasonData(): DropdownData {
  const currentDate = new Date();
  const currentYear = currentDate.getFullYear();

  const indoorStart = new Date(currentYear, 0, 20); // January 20th
  const indoorEnd = new Date(currentYear, 2, 20);   // March 20th

  const availableSeasons: DropdownItem[] = [
    {key: "i", value_en: "Indoor", id: true},
    {key: "o", value_en: "Outdoor", id: false}
  ];

  if (currentDate >= indoorStart && currentDate <= indoorEnd) {
    return {default: "i", items: availableSeasons};
  } else {
    return {default: "o", items: availableSeasons};
  }
}

function generateLimitsData(limits: number[]): DropdownData {
  const items: DropdownItem[] = [];
  limits.forEach((limit) => {items.push({key: limit.toString(), value_en: limit.toString(), id: limit})});
  return {default: limits[1].toString(), items: items};
}

export const formatDate = (date: string): string => {
  const timestamp = Date.parse(date);
  if (isNaN(Date.parse(date))) {
    return date;
  }
  const parsedDate = new Date(timestamp);

  const day = String(parsedDate.getDate()).padStart(2, '0');
  const month = String(parsedDate.getMonth() + 1).padStart(2, '0');
  const year = parsedDate.getFullYear();

  return `${day}.${month}.${year}`;
};

export const formatResult = (performance: number, disciplineType: DisciplineType): string => {
  switch (disciplineType) {
    case DisciplineType.SHORT_TRACK:
    case DisciplineType.JUMP:
    case DisciplineType.THROW:
      return (performance / 100).toFixed(2);

    case DisciplineType.LONG_TRACK:
      {
        const minutes = Math.floor(performance / 6000);
        const seconds = ((performance % 6000) / 100).toFixed(2).padStart(5, "0");
        return `${minutes}:${seconds}`;
      }
    case DisciplineType.MULTI:
    case DisciplineType.DISTANCE:
      return (performance / 100).toString();
  }
}
