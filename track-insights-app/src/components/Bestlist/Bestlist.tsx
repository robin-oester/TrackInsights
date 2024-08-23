import React from "react";

import { Button, Card, CardHeader, CardFooter, Divider } from "@nextui-org/react";
import BestlistTable from "./BestlistTable.tsx";
import BestlistConfiguration from "./BestlistConfiguration.tsx";
import { useBestlist } from "../../hooks/useBestlist.ts";


const Bestlist: React.FC = () => {
  const { bestlistData, handleFetchBestlistData, ...configurationProps} = useBestlist();

  return (
    <div className='flex-col flex justify-center'>
      <Card className="card-max-w mx-auto w-full  mt-10">
        <CardHeader>
          <div className="flex flex-col">
            <p className="text-md">Configuration Section</p>
            <p className="text-small text-default-500">Filter results according to your needs</p>
          </div>
        </CardHeader>
        <Divider/>
        <BestlistConfiguration
          {...configurationProps}
        />
        <CardFooter>
          <Button isDisabled={configurationProps.disciplineId.size == 0} onPress={() => handleFetchBestlistData()} className="mx-auto">
            Find Results
          </Button>
        </CardFooter>
      </Card>

      <div className="pt-10 pb-1 px-1 lg:pb-3 xl:pb-5 lg:px-3 xl:px-5 mx-auto w-full">
        <BestlistTable bestlistData={bestlistData} />
      </div>
    </div>
  )
}

export default Bestlist;
