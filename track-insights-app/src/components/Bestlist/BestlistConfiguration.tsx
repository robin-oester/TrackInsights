import React, { useEffect } from "react";
import {
  AVAILABLE_CATEGORIES,
  AVAILABLE_LIMITS,
  AVAILABLE_RANGE_TYPES,
  AVAILABLE_SEASONS,
  AVAILABLE_YEARS,
  getSelectionId
} from "../../utils/bestlistUtils.ts";
import { fetchDisciplines } from "../../services/disciplinesService.ts";
import { toast } from "sonner";
import {
  CardBody,
  Checkbox,
  Popover,
  PopoverContent,
  PopoverTrigger,
  Select,
  SelectItem,
  Slider
} from "@nextui-org/react";
import { DisciplineItem, DropdownItem } from "../../types/bestlistTypes.ts";
import { DisciplineInformation, DisciplinesRequest } from "../../types/disciplinesTypes.ts";


export interface BestlistConfigurationProps {
  disciplineId: Set<string>;
  setDisciplineId: (disciplineId: Set<string>) => void;
  categoryId: Set<string>;
  setCategoryId: (categoryId: Set<string>) => void;
  yearId: Set<string>;
  setYearId: (yearId: Set<string>) => void;
  seasonId: Set<string>;
  setSeasonId: (seasonId: Set<string>) => void;
  limitId: Set<string>;
  setLimitId: (limitId: Set<string>) => void;
  rangeTypeId: Set<string>;
  setRangeTypeId: (rangeTypeId: Set<string>) => void;
  oneResultPerAthlete: boolean;
  setOneResultPerAthlete: (oneResultPerAthlete: boolean) => void;
  restrictCategory: boolean;
  setRestrictCategory: (restrictCategory: boolean) => void;
  onlyHomologated: boolean;
  setOnlyHomologated: (onlyHomologated: boolean) => void;
  allowWind: boolean;
  setAllowWind: (allowWind: boolean) => void;
  disciplineTouched: boolean;
  setDisciplineTouched: (disciplineTouched: boolean) => void;
  availableDisciplines: (DropdownItem & DisciplineItem)[];
  setAvailableDisciplines: (availableDisciplines: (DropdownItem & DisciplineItem)[]) => void;
  range: [number, number];
  setRange: (disciplineId: [number, number]) => void;
}

const BestlistConfiguration: React.FC<BestlistConfigurationProps> = (
  {
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
    range, setRange
  }
) => {
  const isDisciplineValid = disciplineId.size > 0;

  const selectedYear = React.useMemo(() => {
    return getSelectionId(yearId, AVAILABLE_YEARS);
  }, [yearId]);

  const selectedCategory = React.useMemo(() => {
    return getSelectionId(categoryId, AVAILABLE_CATEGORIES);
  }, [categoryId]);

  const selectedSeason = React.useMemo(() => {
    return getSelectionId(seasonId, AVAILABLE_SEASONS);
  }, [seasonId]);

  const selectedRangeType = React.useMemo(() => {
    return getSelectionId(rangeTypeId, AVAILABLE_RANGE_TYPES);
  }, [rangeTypeId]);

  const selectedDiscipline = React.useMemo(() => {
    if (disciplineId.size > 0) {
      return availableDisciplines.find((val) => val.key === Array.from(disciplineId)[0]);
    }
    return undefined;
    // eslint-disable-next-line
  }, [disciplineId]);

  const disabledRangeKeys = React.useMemo(() => {
    if (!selectedDiscipline || !selectedDiscipline.score_available) {
      return ["score"];
    }
    return [];
  }, [selectedDiscipline]);

  useEffect(() => {
    const params: DisciplinesRequest = {
      year: selectedYear as number | undefined,
      category: selectedCategory as string,
      restrictCategory,
      indoor: selectedSeason as boolean
    };

    fetchDisciplines(params)
      .then((response) => {
        const fetchedDisciplines: (DropdownItem & DisciplineItem)[] = response.disciplines.map((discipline: DisciplineInformation) => ({
          key: discipline.id.toString(),
          value_en: discipline.name,
          id: discipline.id,
          wind_relevant: discipline.wind_relevant,
          score_available: discipline.score_available
        }));
        setAvailableDisciplines(fetchedDisciplines);
        if (disciplineId.size > 0 && !fetchedDisciplines.some((discipline) => discipline.key == Array.from(disciplineId)[0])) {
          setDisciplineId(new Set([]))
        }
      })
      .catch((err) => toast("Could not fetch available disciplines. " + err))
    // eslint-disable-next-line
  }, [selectedYear, selectedCategory, selectedSeason, oneResultPerAthlete, restrictCategory, onlyHomologated]);

  useEffect(() => {
    if (!selectedCategory || selectedCategory == "all_m" || selectedCategory == "all_f") {
      setRestrictCategory(false);
    }
    // eslint-disable-next-line
  }, [selectedCategory]);

  return (
    <CardBody>
      <div className="flex flex-wrap md:flex-nowrap gap-4 flex-1">
        <Select
          label="Year"
          placeholder="Select a year"
          selectionMode="single"
          disallowEmptySelection
          selectedKeys={yearId}
          // @ts-expect-error: Types work correctly
          onSelectionChange={setYearId}
        >
          {AVAILABLE_YEARS.items.map(item => (
            <SelectItem key={item.key}>
              {item.value_en}
            </SelectItem>
          ))}
        </Select>
        <Select
          label="Season"
          placeholder="Select a season"
          selectionMode="single"
          disallowEmptySelection
          selectedKeys={seasonId}
          // @ts-expect-error: Types work correclty
          onSelectionChange={setSeasonId}
        >
          {AVAILABLE_SEASONS.items.map(item => (
            <SelectItem key={item.key}>
              {item.value_en}
            </SelectItem>
          ))}
        </Select>
        <Select
          label="Category"
          placeholder="Select a category"
          selectionMode="single"
          disallowEmptySelection
          selectedKeys={categoryId}
          // @ts-expect-error: Types work correclty
          onSelectionChange={setCategoryId}
        >
          {AVAILABLE_CATEGORIES.items.map(item => (
            <SelectItem key={item.key}>
              {item.value_en}
            </SelectItem>
          ))}
        </Select>
        <Select
          label="Discipline"
          placeholder="Select a discipline"
          selectionMode="single"
          isRequired
          description="The discipline to filter for"
          selectedKeys={disciplineId}
          errorMessage={isDisciplineValid || !disciplineTouched ? "" : "You must select a discipline"}
          isInvalid={!(isDisciplineValid || !disciplineTouched)}
          // @ts-expect-error: Types work correclty
          onSelectionChange={setDisciplineId}
          onClose={() => setDisciplineTouched(true)}
        >
          {availableDisciplines.map(item => (
            <SelectItem key={item.key}>
              {item.value_en}
            </SelectItem>
          ))}
        </Select>
        <Select
          label="Results"
          placeholder="Select number of results"
          selectionMode="single"
          disallowEmptySelection
          className="min-w-34"
          selectedKeys={limitId}
          // @ts-expect-error: Types work correclty
          onSelectionChange={setLimitId}
        >
          {AVAILABLE_LIMITS.items.map(item => (
            <SelectItem key={item.key}>
              {item.value_en}
            </SelectItem>
          ))}
        </Select>
      </div>

      <div className="pt-5 flex flex-col md:flex-row justify-evenly">
        <Checkbox isSelected={oneResultPerAthlete} onValueChange={setOneResultPerAthlete}>One Result Per Athlete</Checkbox>
        <Checkbox isDisabled={!selectedCategory || selectedCategory == "all_m" || selectedCategory == "all_f"} isSelected={restrictCategory} onValueChange={setRestrictCategory}>Restrict Results in this category</Checkbox>
        <Checkbox isSelected={onlyHomologated} onValueChange={setOnlyHomologated}>Only Homologated</Checkbox>
        {selectedDiscipline && selectedDiscipline.wind_relevant && (
          <Checkbox isSelected={allowWind} onValueChange={setAllowWind}>Allow Wind</Checkbox>
        )}
      </div>

      <div className="flex pt-3">
        <Popover placement="bottom" showArrow offset={10}>
          <PopoverTrigger>
            <p className="md:ml-auto underline cursor-pointer">Advanced Settings</p>
          </PopoverTrigger>
          <PopoverContent className="w-[500px]">
            <div className="px-1 py-2 w-full">
              <div className="flex flex-col gap-2 w-full">
                <div className="flex flex-row gap-5 items-center justify-center">
                  <Select
                    aria-label={"Range Filter"}
                    label="Type"
                    size="sm"
                    placeholder="Select filter type"
                    selectionMode="single"
                    className="max-w-[144px]"
                    selectedKeys={rangeTypeId}
                    isDisabled={!selectedDiscipline || !selectedDiscipline.score_available}
                    disabledKeys={disabledRangeKeys}
                    // @ts-expect-error: Types work correclty
                    onSelectionChange={setRangeTypeId}
                  >
                    {AVAILABLE_RANGE_TYPES.items.map(item => (
                      <SelectItem key={item.key} aria-label={item.value_en}>
                        {item.value_en}
                      </SelectItem>
                    ))}
                  </Select>
                  <Slider
                    aria-label={"Range Slider"}
                    label={selectedRangeType ? "Scores": undefined}
                    isDisabled={!selectedDiscipline || !selectedDiscipline.score_available || !selectedRangeType}
                    size="sm"
                    step={1}
                    minValue={0}
                    maxValue={1400}
                    defaultValue={[1, 1400]}
                    value={range}
                    // @ts-expect-error: Types match
                    onChange={setRange}
                    className="max-w-md"
                  />
                </div>
              </div>
            </div>
          </PopoverContent>
        </Popover>
      </div>
    </CardBody>
  )
};

export default BestlistConfiguration;
