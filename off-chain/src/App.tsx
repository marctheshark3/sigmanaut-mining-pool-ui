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
    <Box textAlign="center" fontSize="xl" width="100%" height="100vh">
      <Grid p={0} minH="100%" width="100%">
          <ColorModeSwitcher justifySelf="flex-end" position="absolute" top={2} right={2} zIndex={10} />
          <Tabs width="100%" variant="enclosed" height="100%">
            <TabList>
              {/* <Tab> Mint Sigmanaut Mining Pool Config NFT</Tab> */}
                <Tab fontSize="lg" py={3}> Create Miner ID</Tab>
                <Tab fontSize="lg" py={3}> Burn Miner ID</Tab>
                
        
            </TabList>
            <TabPanels height="calc(100% - 50px)">
            
              <TabPanel height="100%" p={3}>
                <Create />
              </TabPanel>

                <TabPanel height="100%" p={3}>
                <BurnTokens />
              </TabPanel>
             
            </TabPanels>
          </Tabs>
      </Grid>
    </Box>
  </ChakraProvider>
)
