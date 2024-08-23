import React from "react";
import {
  AVAILABLE_CATEGORIES,
  AVAILABLE_LIMITS,
  AVAILABLE_RANGE_TYPES,
  AVAILABLE_SEASONS,
  AVAILABLE_YEARS,
  getInitialValue, getSelectionId
} from "../utils/bestlistUtils.ts";
import { fetchBestlist } from "../services/bestlistService.ts";
import { BestlistRequest, BestlistResponse, DisciplineItem, DropdownItem } from "../types/bestlistTypes.ts";


export const useBestlist = () => {
  const [categoryId, setCategoryId] = React.useState(getInitialValue(AVAILABLE_CATEGORIES));
  const [yearId, setYearId] = React.useState(getInitialValue(AVAILABLE_YEARS));
  const [seasonId, setSeasonId] = React.useState(getInitialValue(AVAILABLE_SEASONS));
  const [limitId, setLimitId] = React.useState(getInitialValue(AVAILABLE_LIMITS));
  const [rangeTypeId, setRangeTypeId] = React.useState(getInitialValue(AVAILABLE_RANGE_TYPES));
  const [oneResultPerAthlete, setOneResultPerAthlete] = React.useState(true);
  const [restrictCategory, setRestrictCategory] = React.useState(false);
  const [onlyHomologated, setOnlyHomologated] = React.useState(true);
  const [allowWind, setAllowWind] = React.useState(false);
  const [availableDisciplines, setAvailableDisciplines] = React.useState<(DropdownItem & DisciplineItem)[]>([]);
  const [disciplineId, setDisciplineId] = React.useState<Set<string>>(new Set([]));
  const [disciplineTouched, setDisciplineTouched] = React.useState(false);
  const [range, setRange] = React.useState<[number, number]>([0, 1400]);

  const [bestlistData, setBestlistData] = React.useState<BestlistResponse | undefined>(undefined);

  const handleFetchBestlistData = () => {
    if (disciplineId.size == 0) {
      return;
    }
    const selectedDiscipline = availableDisciplines.find((val) => val.key === Array.from(disciplineId)[0]) as (DisciplineItem & DropdownItem);

    const params: BestlistRequest = {
      year: getSelectionId(yearId, AVAILABLE_YEARS) as number | undefined,
      category: getSelectionId(categoryId, AVAILABLE_CATEGORIES) as string,
      disciplineId: selectedDiscipline.id as number,
      onlyHomologated,
      restrictCategory,
      oneResultPerAthlete,
      allowWind,
      rangeType: selectedDiscipline.score_available ? (getSelectionId(rangeTypeId, AVAILABLE_RANGE_TYPES) as string | undefined) : undefined,
      rangeStart: range[0],
      rangeEnd: range[1],
      limit: getSelectionId(limitId, AVAILABLE_LIMITS) as number
    };

    fetchBestlist(params)
      .then(setBestlistData)
      .catch(err => console.error("Error fetching bestlist: " + err))
  };

  return {
    disciplineId, setDisciplineId,
    categoryId, setCategoryId,
    yearId, setYearId,
    seasonId, setSeasonId,
    limitId, setLimitId,
    rangeTypeId, setRangeTypeId,
    oneResultPerAthlete, setOneResultPerAthlete,
    restrictCategory, setRestrictCategory,
    onlyHomologated, setOnlyHomologated,
    allowWind, setAllowWind,
    disciplineTouched, setDisciplineTouched,
    availableDisciplines, setAvailableDisciplines,
    range, setRange,
    bestlistData,
    handleFetchBestlistData
  }
}
