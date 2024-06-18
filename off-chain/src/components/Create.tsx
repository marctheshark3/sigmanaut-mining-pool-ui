import React, { useState, useEffect } from 'react';
import Papa from 'papaparse';
import {
    Alert,
    AlertIcon,
    Button,
    FormControl,
    FormLabel,
    NumberInputField,
    NumberInput,
    NumberInputStepper,
    NumberIncrementStepper,
    NumberDecrementStepper,
    Stack,
    VStack,
    Select,
    Link, // Import Link from Chakra UI
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

interface Token {
    'Token Name': string;
}

interface SelectedToken {
    token: string;
    value: number;
}

function Create() {
    const [minimumPayout, setMinimumPayout] = useState<number>(0.01);
    const [created, setCreated] = useState<boolean>(false);
    const [tx, setTx] = useState<string>('...');
    const [error, setError] = useState<string>('');
    const [tokens, setTokens] = useState<Token[]>([]);
    const [selectedTokens, setSelectedTokens] = useState<SelectedToken[]>([{ token: '', value: 0 }]);

    useEffect(() => {
        // Load the CSV file from the public directory
        fetch('/supported-tokens.csv')
            .then(response => response.text())
            .then(data => {
                Papa.parse<Token>(data, {
                    header: true,
                    complete: (results) => {
                        setTokens(results.data);
                    },
                });
            });
    }, []);

    const handleMinimumPayoutChange = (valueAsString: string, valueAsNumber: number) => {
        setMinimumPayout(valueAsNumber);
    };

    const handleTokenChange = (index: number, field: keyof SelectedToken, value: string | number) => {
        const newSelectedTokens = [...selectedTokens];
        newSelectedTokens[index][field] = value as never;
        setSelectedTokens(newSelectedTokens);
    };

    const handleAddToken = () => {
        setSelectedTokens([...selectedTokens, { token: '', value: 0 }]);
    };

    const handleSubmit = () => {
        const totalValue = selectedTokens.reduce((sum, token) => sum + token.value, 0);
        if (totalValue !== 100) {
            setError('The sum of all token values must add up to 100.');
            return;
        } else {
            setError('');
            create_token(minimumPayout, selectedTokens);
        }
    };

    async function create_token(minimumPayout: number, selectedTokens: SelectedToken[]): Promise<void> {
        connected = await window.ergoConnector.nautilus.connect();
        if (connected) {
            const address = await ergo.get_change_address();
            const height = await ergo.get_current_height();
            const nftName = 'Sigmanaut Mining Pool Configuration NFT - Season 0';

            const dictionary = {
                address: address,
                minimumPayout: minimumPayout,
                tokens: selectedTokens,
                text: 'This is a test token minted with Fleet SDK for the sigmanaut mining pool'
            };
            const dictionaryString = JSON.stringify(dictionary);

            const unsignedTx = new TransactionBuilder(height)
                .from(await ergo.get_utxos())
                .to(
                    new OutputBuilder("1000000", address)
                    .mintToken({
                        amount: "1",
                        name: nftName,
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
            <Title title='Mint token' />
            <FormControl>
                <Stack spacing={3}>

                    <FormLabel>Minimum Payout</FormLabel>
                    <NumberInput min={0} value={minimumPayout} onChange={handleMinimumPayoutChange} precision={2} step={0.01}>
                        <NumberInputField />
                        <NumberInputStepper>
                            <NumberIncrementStepper />
                            <NumberDecrementStepper />
                        </NumberInputStepper>
                    </NumberInput>

                    {selectedTokens.map((selectedToken, index) => (
                        <div key={index}>
                            <FormLabel>Select Token</FormLabel>
                            <Select
                                placeholder='Select token'
                                value={selectedToken.token}
                                onChange={(e) => handleTokenChange(index, 'token', e.target.value)}
                            >
                                {tokens.map((token, i) => (
                                    <option key={i} value={token['Token Name']}>
                                        {token['Token Name']}
                                    </option>
                                ))}
                            </Select>
                            <FormLabel>Enter Value</FormLabel>
                            <NumberInput
                                min={0}
                                value={selectedToken.value}
                                onChange={(valueAsString, valueAsNumber) => handleTokenChange(index, 'value', valueAsNumber)}
                            >
                                <NumberInputField />
                                <NumberInputStepper>
                                    <NumberIncrementStepper />
                                    <NumberDecrementStepper />
                                </NumberInputStepper>
                            </NumberInput>
                        </div>
                    ))}

                    <Button onClick={handleAddToken}>Add Token</Button>

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
                            <Link href={`https://ergexplorer.com/transactions/${tx}`} isExternal>
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
