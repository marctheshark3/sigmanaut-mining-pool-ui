import React, { useState, ChangeEvent } from 'react';
import Token from '../components/Token';

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
    NumberInputField,
    NumberInput,
    NumberInputStepper,
    NumberIncrementStepper,
    NumberDecrementStepper,
    Stack,
    VStack,
} from '@chakra-ui/react'

import { OutputBuilder, TransactionBuilder } from "@fleet-sdk/core";

import Title from '../components/Title';

declare global {
  interface Window {
    ergoConnector: any;
  }
}
declare var ergo: any;
var connected: any;

function SendTokens() {

    const [wallet, setWallet] = useState<string>('');
    const [tokenID, setTokenID] = useState<string>('');
    const [amount, setAmount] = useState<number>(1);

    const [sent, setSent] = useState(false);
    const [tx, setTx] = useState('...');

    const [tokenDetails, setTokenDetails] = useState({ id: '', name: '', description: '', decimals: 0, emissionAmount: 0, type: '', boxId: '' });
    const [visible, setVisible] = useState(false)

    const handleTokenNameChange = (event: ChangeEvent<HTMLInputElement>) => {
        setWallet(event.target.value);
    }

    const handleTokenIDChange = async (event: ChangeEvent<HTMLInputElement>) => {
        const tokenId = event.target.value;
        setTokenID(tokenId);

        try {
            const response = await fetch(`https://api.ergoplatform.com/api/v1/tokens/${tokenId}`);
            if (!response.ok) {
                throw new Error('Error with API');
            }
            const data = await response.json();
            setTokenDetails(data);
            setVisible(true)
        } catch (error) {
            console.error('Error:', error);
        }
    }

    const handleAmountChange = (valueAsString: string, valueAsNumber: number) => {
        setAmount(valueAsNumber);
    }

    const handleSubmit = () => {
        create_token(wallet, amount, tokenID)
    }

    async function create_token(wallet: string, amount: any, tokenID: any): Promise<void> { 
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
                amount: amount, 
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
            <Title title='Send tokens'/>
            <FormControl>
                <Stack spacing={3}>

                    <FormLabel>Destination wallets</FormLabel>
                    <Input 
                        placeholder='Enter destination wallet' 
                        size='md' 
                        value={wallet}
                        onChange={handleTokenNameChange}
                        />

                    <FormLabel>Token ID</FormLabel>
                    <Input 
                        placeholder='Enter token ID' 
                        size='md' 
                        value={tokenID}
                        onChange={handleTokenIDChange}
                        />
                    
                    <FormLabel>Amount</FormLabel>
                    <NumberInput 
                        min={1} 
                        value={amount} 
                        onChange={handleAmountChange}
                        precision={1} step={1} >
                        <NumberInputField />
                        <NumberInputStepper>
                        <NumberIncrementStepper />
                        <NumberDecrementStepper />
                        </NumberInputStepper>
                    </NumberInput>

                    <Button colorScheme='teal' variant='outline' onClick={handleSubmit}> 
                        Send
                    </Button>

                    {visible && (
                            <Box textAlign={'left'}>
                                <Heading size='md' mt={5} mb={3}>Token details</Heading>
                                <Token 
                                        id={tokenDetails.id}
                                        name={tokenDetails.name}
                                        description={tokenDetails.description}
                                        decimals={tokenDetails.decimals}
                                        emissionAmount={tokenDetails.emissionAmount}
                                        type={tokenDetails.type}
                                        boxId={tokenDetails.boxId}
                                    />
                            </Box>
                    )}
                    
                    {sent && (
                        <VStack>
                            <Alert status='success' variant='solid'>
                                <AlertIcon />
                                Tokens sent successfully!
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

export default SendTokens;