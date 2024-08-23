import React from "react";

import { Table, TableBody, TableCell, TableColumn, TableHeader, TableRow } from "@nextui-org/react";
import { formatDate, formatResult } from "../../utils/bestlistUtils.ts";
import { BestlistItem, ConfigurationInformation, DisciplineType } from "../../types/bestlistTypes.ts";


interface BestlistData {
  configuration: ConfigurationInformation;
  results: BestlistItem[];
}

export interface BestlistTableProps {
  bestlistData?: BestlistData;
}

const BestlistTable: React.FC<BestlistTableProps> = React.memo(({ bestlistData }) => {
  if (!bestlistData || bestlistData.results.length === 0) {
    return (
      <Table aria-label="Empty table">
        {
          generateTableHeader({
            wind_relevant: false,
            homologation_relevant: false,
            score_available: false,
            discipline_type: DisciplineType.SHORT_TRACK
          })
        }
        <TableBody emptyContent={"No rows to display."}>{[]}</TableBody>
      </Table>
    );
  }

  const { results, configuration } = bestlistData;
  const computedRanks = computeRanks(results);
  return (
    <Table isStriped className="pt-2" aria-label="Bestlist Table">
      {generateTableHeader(configuration)}
      <TableBody>
        {results.map((row, idx) => (
          <TableRow key={idx.toString()}>
            {getTableRow(configuration, row, idx.toString(), computedRanks[idx])}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
});

function getBestlistTableHeaders(configuration: ConfigurationInformation): string[] {
  const headers: string[] = [];
  headers.push("Nr");
  headers.push("Resultat");
  if (configuration.wind_relevant) {
    headers.push("Wind");
  }
  headers.push("Rang");
  if (configuration.homologation_relevant) {
    headers.push("NH*");
  }
  headers.push("Name");
  headers.push("Club");
  headers.push("Nat.");
  headers.push("Geb. Dat.");
  headers.push("Wettkampf");
  headers.push("Ort");
  headers.push("Datum");
  if (configuration.score_available) {
    headers.push("Punkte");
  }
  return headers;
}

function generateTableHeader(configuration: ConfigurationInformation): JSX.Element {
  return (
    <TableHeader>
      {getBestlistTableHeaders(configuration).map(header => (
        <TableColumn key={header}>{header}</TableColumn>
      ))}
    </TableHeader>
  );
}

function getTableRow(configuration: ConfigurationInformation, row: BestlistItem, idx: string, rank: number): JSX.Element[] {
  const cells: JSX.Element[] = [];
  cells.push(<TableCell key={idx + ".1"}>{rank.toString()}</TableCell>);
  cells.push(<TableCell key={idx + ".2"}>{formatResult(row.result.performance, configuration.discipline_type)}</TableCell>);
  if (configuration.wind_relevant) {
    cells.push(<TableCell key={idx + ".3"}>{row.result.wind}</TableCell>);
  }
  cells.push(<TableCell key={idx + ".4"}>{row.result.rank}</TableCell>);
  if (configuration.homologation_relevant) {
    cells.push(<TableCell key={idx + ".5"}>{!row.result.homologated ? "X" : ""}</TableCell>);
  }
  cells.push(<TableCell key={idx + ".6"}>{row.athlete.name}</TableCell>);
  cells.push(<TableCell key={idx + ".7"}>{row.club.name}</TableCell>);
  cells.push(<TableCell key={idx + ".8"}>{row.athlete.nationality}</TableCell>);
  cells.push(<TableCell key={idx + ".9"}>{formatDate(row.athlete.birthdate)}</TableCell>);
  cells.push(<TableCell key={idx + ".10"}>{row.event.name}</TableCell>);
  cells.push(<TableCell key={idx + ".11"}>{row.result.location}</TableCell>);
  cells.push(<TableCell key={idx + ".12"}>{formatDate(row.result.date)}</TableCell>);
  if (configuration.score_available) {
    cells.push(<TableCell key={idx + ".13"}>{row.result.points}</TableCell>);
  }
  return cells;
}

const computeRanks = (rows: BestlistItem[]) => {
  const ranks: number[] = [];
  let currentRank = 1;

  rows.forEach((row, idx) => {
    if (idx === 0) {
      ranks.push(currentRank);
    } else {
      if (row.result.performance === rows[idx - 1].result.performance) {
        ranks.push(currentRank);
      } else {
        currentRank = idx + 1;
        ranks.push(currentRank);
      }
    }
  });
  return ranks;
}

export default BestlistTable;
