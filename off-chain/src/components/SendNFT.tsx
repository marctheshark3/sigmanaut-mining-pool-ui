import React, { useState, ChangeEvent } from 'react';

import { 
    Alert,
    AlertIcon,
    Box,
    Button,
    FormControl,
    FormLabel,
    Heading,
    Input ,
    Link,
    Stack,
    VStack,
} from '@chakra-ui/react'

import { OutputBuilder, TransactionBuilder } from "@fleet-sdk/core";
import Title from '../components/Title';
import Nft from './Nft';
import { resolveIpfs, toUtf8String } from '../functions/Functions'

declare global {
  interface Window {
    ergoConnector: any;
  }
}
declare var ergo: any;
var connected: any;


function SendNFT() {

    const [wallet, setWallet] = useState<string>('');
    const [tokenID, setTokenID] = useState<string>('');

    const [sent, setSent] = useState(false);
    const [tx, setTx] = useState('...');

    const handleTokenNameChange = (event: ChangeEvent<HTMLInputElement>) => {
        setWallet(event.target.value);
    }
    
    const handleSubmit = () => {
        sendNft(wallet, tokenID)
    }
    
    const [tokenDetails, setTokenDetails] = useState<{ name: string; description: string; r9: string; }>({
        name: '',
        description: '',
        r9: '',
    });
    
    const [visible, setVisible] = useState(false)

    const handleTokenIDChange = async (event: ChangeEvent<HTMLInputElement>) => {
        const tokenId = event.target.value;
        setTokenID(tokenId);

        try {
            const response = await fetch(`https://api.ergoplatform.com/api/v0/assets/${tokenId}/issuingBox`);
            if (!response.ok) {
                throw new Error('Error with API');
            }
            const data = await response.json();
            setTokenDetails({
                name: data[0].assets[0].name,
                description: toUtf8String(data[0].additionalRegisters.R5).substring(2),
                r9: resolveIpfs(toUtf8String(data[0].additionalRegisters.R9).substring(2))
            });
            setVisible(true)
        } catch (error) {
            console.error('Error:', error);
        }
    }

    async function sendNft(wallet: string, tokenID: any): Promise<void> { 
        connected = await window.ergoConnector.nautilus.connect(); 
        if (connected) {
          const height = await ergo.get_current_height();
          const unsignedTx = new TransactionBuilder(height)
            .from(await ergo.get_utxos())
            .to(
              new OutputBuilder(
                "1000000", wallet
              )
            .addTokens({ 
                tokenId: tokenID,
                amount: "1", 
              })
            )
            .sendChangeTo(await ergo.get_change_address())
            .payMinFee()
            .build()
            .toEIP12Object();
          const signedTx = await ergo.sign_tx(unsignedTx);
          const txId = await ergo.submit_tx(signedTx);
          setTx(txId);
          setSent(true)
        }
    }

    return (
        <>
            <Title title='Send NFT'/>
            <FormControl>
                <Stack spacing={3}>

                    <FormLabel>Destination wallet</FormLabel>
                    <Input 
                        placeholder='Enter destination wallet' 
                        size='md' 
                        value={wallet}
                        onChange={handleTokenNameChange}
                        />

                    <FormLabel>NFT ID</FormLabel>
                    <Input 
                        placeholder='Enter NFT ID' 
                        size='md' 
                        value={tokenID}
                        onChange={handleTokenIDChange}
                        />
                        
                    <Button colorScheme='teal' variant='outline' onClick={handleSubmit}> 
                        Send
                    </Button>

                    {visible && (
                        <Box textAlign={'left'}>
                            <Heading size='md' mt={5} mb={3}>Token details</Heading>
                            <Nft 
                                    r9={tokenDetails.r9}
                                    name={tokenDetails.name}
                                    description={tokenDetails.description}
                                />
                        </Box>
                    )}
                    
                    {sent && (
                        <VStack>
                            <Alert status='success' variant='solid'>
                                <AlertIcon />
                                NFT sent successfully!
                            </Alert>

                            <Link href={`https://explorer.ergoplatform.com/en/transactions/${tx}`} isExternal>
                                {tx}
                            </Link>
                        </VStack>
                    )}

                </Stack>
            </FormControl>
            
        </>
    );
};

export default SendNFT;