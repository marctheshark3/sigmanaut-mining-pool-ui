import React, { useEffect, useState } from 'react';
import {
  ChakraProvider,
  Box,
  Grid,
  theme,
  Text,
} from "@chakra-ui/react";
import { ColorModeSwitcher } from "./ColorModeSwitcher";

import { OutputBuilder, TransactionBuilder } from "@fleet-sdk/core";

declare global {
  interface Window {
    ergoConnector: any;
  }
}
declare var ergo: any;
var connected: any;

export const App = () => {

  const [tx, setTx] = useState('...');

  useEffect(() => {
    send_token();
  }, []);

  async function send_token(): Promise<void> {
 
    connected = await window.ergoConnector.nautilus.connect(); 
    if (connected) {
      const balance = await ergo.get_balance("all");
      const addr = await ergo.get_change_address();
      // const wallet = '9eg7v2nkypUZbdyvSKSD9kg8FNwrEdTrfC2xdXWXmEpDAFEtYEn'
      await ergo.address
      const myText = `This is a test token minted with Fleet SDK for the sigmanaut mining pool for the miner ${addr} with a balance of $`;
      console.log(myText);
      console.log(balance);
      const height = await ergo.get_current_height();
      const unsignedTx = new TransactionBuilder(height)

      

        .from(await ergo.get_utxos())
        .to(
          [new OutputBuilder('2000000', '9hAcdWpFAv7biCSeUcCvXWYRfEepm1ubdsfg5PC48k9S7ymiU3W'),
          new OutputBuilder(
            "1000000", addr 
          new OutputBuilder('2000000', '')
          )
          .mintToken({ 
            amount: "1", // the amount of tokens being minted without decimals 
            name: "TESTSIGMAPOOL-NFT-5", // the name of the token 
            decimals: 0, // the number of decimals  
            description: myText 
          }) ]
          // .addTokens({ 
          //   tokenId: 
          //     "865484a243cfbf203c47fde0191dfd4fc0e05e876a61365a265055be299f2335",
          //   amount: "1", 
          // }) 
        )
        .sendChangeTo(await ergo.get_change_address())
        .payMinFee()
        .build()
        .toEIP12Object();
      const signedTx = await ergo.sign_tx(unsignedTx);
      const txId = await ergo.submit_tx(signedTx);
      setTx(txId);
    }
  }

  return (
    <ChakraProvider theme={theme}>
      <Box textAlign="center" fontSize="xl">
        <Grid minH="100vh" p={3}>
          <ColorModeSwitcher justifySelf="flex-end" />
          <Text as='mark'>
            tx ID: {tx}
          </Text>
        </Grid>
      </Box>
    </ChakraProvider>
  );
};
