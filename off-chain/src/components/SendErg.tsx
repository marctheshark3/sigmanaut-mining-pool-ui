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

function SendERG() {

    const [wallet, setWallet] = useState<string>('');
    const [amount, setAmount] = useState<number>(0.001);

    const [sent, setSent] = useState(false);
    const [tx, setTx] = useState('...');


    const handleTokenNameChange = (event: ChangeEvent<HTMLInputElement>) => {
        setWallet(event.target.value);
    }

    const handleAmountChange = (valueAsString: string, valueAsNumber: number) => {
        setAmount(valueAsNumber);
    }

    const handleSubmit = () => {
        create_token(wallet, amount)
    }

    async function create_token(wallet: string, amount: number): Promise<void> { 
        connected = await window.ergoConnector.nautilus.connect(); 
        if (connected) {
          const height = await ergo.get_current_height();
          const unsignedTx = new TransactionBuilder(height)
            .from(await ergo.get_utxos())
            .to(
              new OutputBuilder(
                BigInt(amount * 1e9), wallet
              )
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
            <Title title='Send ERG'/>
            <FormControl>
                <Stack spacing={3}>

                    <FormLabel>Destination wallets</FormLabel>
                    <Input 
                        placeholder='Enter destination wallet' 
                        size='md' 
                        value={wallet}
                        onChange={handleTokenNameChange}
                        />
                    
                    <FormLabel>Amount</FormLabel>
                    <NumberInput 
                        min={0.001} 
                        value={amount} 
                        onChange={handleAmountChange}
                        precision={6} step={0.001} >
                        <NumberInputField />
                        <NumberInputStepper>
                        <NumberIncrementStepper />
                        <NumberDecrementStepper />
                        </NumberInputStepper>
                    </NumberInput>

                        
                    <Button colorScheme='teal' variant='outline' onClick={handleSubmit}> 
                        Send
                    </Button>
                    
                    
                    {sent && (
                        <VStack>
                            <Alert status='success' variant='solid'>
                                <AlertIcon />
                                ERG sent successfully!
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

export default SendERG;