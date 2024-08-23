import axios from 'axios';

import { API_BASE_URL } from '../utils/bestlistUtils.ts';
import { DisciplinesRequest, DisciplinesResponse } from "../types/disciplinesTypes.ts";


export const fetchDisciplines = async (request: DisciplinesRequest): Promise<DisciplinesResponse> => {
  try {
    const params: Record<string, unknown> = {
      "year": request.year,
      "category_identifier": request.category,
      "indoor": request.indoor,
      "restrict_category": request.restrictCategory,
    };

    const response = await axios.get<DisciplinesResponse>(`${API_BASE_URL}/disciplines/`, {
      params
    });
    return response.data;
  } catch (error) {
    console.error("Error fetching disciplines:", error);
    throw error;
  }
};
