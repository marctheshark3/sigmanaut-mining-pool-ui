import React, { useState, ChangeEvent } from 'react';

import { 
    Alert,
    AlertIcon,
    Button,
    FormControl,
    FormLabel,
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

function BurnTokens() {

    const [tokenID, setTokenID] = useState<string>('');
    const [amount, setAmount] = useState<number>(1);

    const [burn, setBurn] = useState(false);
    const [tx, setTx] = useState('...');

    const handleTokenIDChange = (event: ChangeEvent<HTMLInputElement>) => {
        setTokenID(event.target.value);
    }

    const handleAmountChange = (valueAsString: string, valueAsNumber: number) => {
        setAmount(valueAsNumber);
    }

    const handleSubmit = () => {
        create_token(amount, tokenID)
    }

    async function create_token(amount: any, tokenID: any): Promise<void> { 
        connected = await window.ergoConnector.nautilus.connect(); 
        if (connected) {
          const height = await ergo.get_current_height();
          const unsignedTx = new TransactionBuilder(height)
            .burnTokens({ 
                tokenId: tokenID, 
                amount: amount
            })

            .from(await ergo.get_utxos())
            .sendChangeTo(await ergo.get_change_address())
            .payMinFee()
            .build()
            .toEIP12Object();
          const signedTx = await ergo.sign_tx(unsignedTx);
          const txId = await ergo.submit_tx(signedTx);
          setTx(txId);
          setBurn(true)
        }
    }

    return (
        <>
            <Title title='Burn tokens'/>
            
            <FormControl>
                <Stack spacing={3}>

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

                        
                    <Button bg='#E53E3E' variant='outline' onClick={handleSubmit}> 
                        Burn
                    </Button>
                    
                    
                    {burn && (
                        <VStack>
                            <Alert status='success' variant='solid'>
                                <AlertIcon />
                                Tokens burned successfully!
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

export default BurnTokens;