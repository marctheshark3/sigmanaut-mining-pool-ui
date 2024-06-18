import * as React from "react"

import {
  Box,
  ChakraProvider,
  Grid,
  Tab, 
  Tabs, 
  TabList, 
  TabPanel, 
  TabPanels, 
  theme,
} from "@chakra-ui/react"
import { ColorModeSwitcher } from "./ColorModeSwitcher"

import Create from './components/Create';
import BurnTokens from './components/BurnTokens';

export const App = () => (
  
  <ChakraProvider theme={theme}>
    <Box textAlign="center" fontSize="xl">
      <Grid p={3}>
          <ColorModeSwitcher justifySelf="flex-end" />
          <Tabs>
            <TabList>
              {/* <Tab> Mint Sigmanaut Mining Pool Config NFT</Tab> */}
                <Tab> Create Miner ID</Tab>
                <Tab> Burn Miner ID</Tab>
                
        
            </TabList>
            <TabPanels>
            
              <TabPanel>
                <Create />
              </TabPanel>

                <TabPanel>
                <BurnTokens />
              </TabPanel>
             
            </TabPanels>
          </Tabs>
      </Grid>
    </Box>
  </ChakraProvider>
)
