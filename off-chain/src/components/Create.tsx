import React, { useState } from 'react';
import { 
    Alert,
    AlertIcon,
    Button,
    FormControl,
    FormLabel,
    Input,
    Link,
    NumberInputField,
    NumberInput,
    NumberInputStepper,
    NumberIncrementStepper,
    NumberDecrementStepper,
    Stack,
    VStack,
} from '@chakra-ui/react';
import { OutputBuilder, TransactionBuilder } from "@fleet-sdk/core";
import Title from '../components/Title';

declare global {
  interface Window {
    ergoConnector: any;
  }
}
declare var ergo: any;
var connected: any;

function Create() {
    const [minimumPayout, setminimumPayout] = useState(0);
    const [erg_ratio, set_erg_ratio] = useState(0);
    const [rsn_ratio, set_rsn_ratio] = useState(0);
    const [created, setCreated] = useState(false);
    const [tx, setTx] = useState('...');
    const [error, setError] = useState('');

    const handle_erg_ratioChange = (valueAsString: string, valueAsNumber: number) => {
        set_erg_ratio(valueAsNumber);
    };

    const handle_rsn_ratioChange = (valueAsString: string, valueAsNumber: number) => {
        set_rsn_ratio(valueAsNumber);
    };

    const handleminimumPayoutChange = (valueAsString: string, valueAsNumber: number) => {
        setminimumPayout(valueAsNumber);
    };

    const handleSubmit = () => {
        if (erg_ratio + rsn_ratio !== 100) {
            setError('Ergo ratio and RSN ratio must add up to 100.');
            return;
        } else {
            setError('');
            create_token(minimumPayout, erg_ratio, rsn_ratio);
        }
    };

    async function create_token(minimumPayout: any, erg_ratio: any, rsn_ratio: any): Promise<void> { 
        connected = await window.ergoConnector.nautilus.connect(); 
        if (connected) {
            const address = await ergo.get_change_address();
            const height = await ergo.get_current_height();
            const nft_name = 'Sigmanaut Mining Pool Configuration NFT - Season 0';

            const dictionary = {
                address: address,
                erg: erg_ratio,
                rsn: rsn_ratio,
                minimumPayout: minimumPayout,
                description: 'This is a test token minted with Fleet SDK for the sigmanaut mining pool'
            };
            const dictionaryString = JSON.stringify(dictionary);

            const unsignedTx = new TransactionBuilder(height)
                .from(await ergo.get_utxos())
                .to(
                    new OutputBuilder("1000000", address)
                    .mintToken({ 
                        amount: "1",
                        name: nft_name,
                        decimals: 0,
                        description: dictionaryString
                    })
                )
                .sendChangeTo(await ergo.get_change_address())
                .payMinFee()
                .build()
                .toEIP12Object();
            const signedTx = await ergo.sign_tx(unsignedTx);
            const txId = await ergo.submit_tx(signedTx);
            setTx(txId);
            setCreated(true);
        }
    }

    return (
        <>
            <Title title='Mint token'/>
            <FormControl>
                <Stack spacing={3}>
                    <FormLabel>Ergo Ratio %</FormLabel>
                    <NumberInput min={1} value={erg_ratio} onChange={handle_erg_ratioChange}>
                        <NumberInputField />
                        <NumberInputStepper>
                            <NumberIncrementStepper />
                            <NumberDecrementStepper />
                        </NumberInputStepper>
                    </NumberInput>

                    <FormLabel>RSN Ratio %</FormLabel>
                    <NumberInput min={1} value={rsn_ratio} onChange={handle_rsn_ratioChange}>
                        <NumberInputField />
                        <NumberInputStepper>
                            <NumberIncrementStepper />
                            <NumberDecrementStepper />
                        </NumberInputStepper>
                    </NumberInput>

                    <FormLabel>Minimum Payout</FormLabel>
                    <NumberInput min={0} value={minimumPayout} onChange={handleminimumPayoutChange}>
                        <NumberInputField />
                        <NumberInputStepper>
                            <NumberIncrementStepper />
                            <NumberDecrementStepper />
                        </NumberInputStepper>
                    </NumberInput>

                    {error && (
                        <Alert status='error' variant='solid'>
                            <AlertIcon />
                            {error}
                        </Alert>
                    )}

                    <Button colorScheme='teal' variant='outline' onClick={handleSubmit}> 
                        Mint NFT
                    </Button>

                    {created && (
                        <VStack>
                            <Alert status='success' variant='solid'>
                                <AlertIcon />
                                Token successfully created!
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
}

export default Create;
