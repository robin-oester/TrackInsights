export interface BestlistRequest {
  year?: number,
  category: string,
  disciplineId: number,
  onlyHomologated: boolean,
  restrictCategory: boolean,
  oneResultPerAthlete: boolean,
  allowWind: boolean,
  rangeType?: string,
  rangeStart: number,
  rangeEnd: number,
  limit: number
}

export interface BestlistResponse {
  configuration: ConfigurationInformation;
  results: BestlistItem[];
}

export interface ConfigurationInformation {
  wind_relevant: boolean;
  homologation_relevant: boolean;
  score_available: boolean;
  discipline_type: DisciplineType;
}

export interface BestlistItem {
  athlete: AthleteInformation;
  club: ClubInformation;
  event: EventInformation;
  result: ResultInformation;
}

export enum DisciplineType {
  THROW = "THROW",
  SHORT_TRACK = "SHORT_TRACK",
  LONG_TRACK = "LONG_TRACK",
  JUMP = "JUMP",
  MULTI = "MULTI",
  DISTANCE = "DISTANCE"
}

export interface AthleteInformation {
  id: number;
  name: string;
  nationality: string;
  birthdate: string;
}

export interface ClubInformation {
  id: number;
  name: string;
}

export interface EventInformation {
  id: number;
  name: string;
}

export interface ResultInformation {
  performance: number;
  wind?: number;
  rank: string;
  location: string;
  date: string;
  homologated: boolean;
  points: number;
}

export interface DropdownData {
  default?: string;
  items: DropdownItem[];
}

export interface DropdownItem {
  key: string;
  value_en: string;
  value_de?: string;
  id: string | number | boolean | null;
}

export interface DisciplineItem {
  wind_relevant: boolean
  score_available: boolean
}

export type SelectionType = undefined | string | number | boolean;
