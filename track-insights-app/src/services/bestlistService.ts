import axios from 'axios';

import { API_BASE_URL } from '../utils/bestlistUtils.ts';
import { BestlistRequest, BestlistResponse } from "../types/bestlistTypes.ts";


export const fetchBestlist = async (request: BestlistRequest): Promise<BestlistResponse> => {
  try {
    const params: Record<string, unknown> = {
      "year": request.year,
      "category_identifier": request.category,
      "discipline_id": request.disciplineId,
      "only_homologated": request.onlyHomologated,
      "restrict_category": request.restrictCategory,
      "one_result_per_athlete": request.oneResultPerAthlete,
      "allow_wind": request.allowWind,
      "range_type": request.rangeType,
      "range_start": request.rangeStart,
      "range_end": request.rangeEnd,
      "limit": request.limit
    };

    const response = await axios.get<BestlistResponse>(`${API_BASE_URL}/bestlist/`, {
      params
    });
    return response.data;
  } catch (error) {
    console.error("Error fetching bestlist:", error);
    throw error;
  }
};
