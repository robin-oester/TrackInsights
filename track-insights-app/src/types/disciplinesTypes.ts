export interface DisciplinesRequest {
  year?: number,
  category: string,
  restrictCategory: boolean,
  indoor: boolean,
}

export interface DisciplineInformation {
  id: number,
  name: string,
  score_available: boolean,
  wind_relevant: boolean,
}

export interface DisciplinesResponse {
  disciplines: DisciplineInformation[]
}
