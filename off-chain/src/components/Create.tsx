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
    Link,
   // Text,
    useToast,
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
    const [hasReceiptToken, setHasReceiptToken] = useState<boolean | null>(null);
    const [isChecking, setIsChecking] = useState<boolean>(false);
    const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
    const toast = useToast();

    // Define the receipt token ID and other constants
    const RECEIPT_TOKEN_ID = "ff9318934c9420f595f314eebc7188df7d8b4a7beb0fccc5b28e8ab272bb6e1b";
   // const RECEIPT_TOKEN_AMOUNT = "1"; // Amount of receipt token to send
    const FEE_AMOUNT = "3000000000"; // 3 ERG in nanoERGs
    const FEE_ADDRESS ="9fA4RypzYiYNKHkcWjo1V2AYLA5Z3ny7bgVKBTdpQKrkaR38eJU"; // MARCS "9eg7v2nkypUZbdyvSKSD9kg8FNwrEdTrfC2xdXWXmEpDAFEtYEn";

    useEffect(() => {
        fetch('https://raw.githubusercontent.com/marctheshark3/Mining-Reward-Tokens/main/supported-swap-tokens.csv')
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

    const checkWalletForReceiptToken = async () => {
        setIsChecking(true);
        setError('');
        try {
            if (!window.ergoConnector) {
                throw new Error("Ergo connector not found. Please make sure you have Nautilus wallet installed.");
            }

            connected = await window.ergoConnector.nautilus.connect();
            if (!connected) {
                throw new Error("Failed to connect to the wallet. Please try again.");
            }

            const address = await ergo.get_change_address();
            if (!address) {
                throw new Error("Failed to get wallet address. Please check your wallet connection.");
            }

            const utxos = await ergo.get_utxos();
            if (!Array.isArray(utxos)) {
                throw new Error("Failed to retrieve UTXOs from the wallet.");
            }

            const hasToken = utxos.some((utxo: any) => 
                utxo.assets && Array.isArray(utxo.assets) && utxo.assets.some((asset: any) => 
                    asset.tokenId === RECEIPT_TOKEN_ID
                )
            );
            
            setHasReceiptToken(hasToken);
            console.log(`voucher token check result: ${hasToken ? "voucher token found" : "voucher token not found"}`);
        } catch (error) {
            console.error("Error checking wallet:", error);
            setError(error instanceof Error ? error.message : "An unknown error occurred while checking the wallet.");
            setHasReceiptToken(null);
        } finally {
            setIsChecking(false);
        }
    };

    const handleSubmit = async () => {
        const totalValue = selectedTokens.reduce((sum, token) => sum + token.value, 0);
        if (totalValue !== 100) {
            setError('The sum of all token values must add up to 100.');
            return;
        } else {
            setError('');
            if (hasReceiptToken === null) {
                setError('Please check your wallet for the voucher token first.');
                return;
            }
            try {
                setIsSubmitting(true);
                await create_token(minimumPayout, selectedTokens);
            } catch (error) {
                handleTransactionError(error);
            } finally {
                setIsSubmitting(false);
            }
        }
    };

    const handleTransactionError = (error: any) => {
        console.error("Transaction error:", error);
        if (error.info === "Canceled") {
            toast({
                title: "Transaction Canceled",
                description: "The transaction was canceled. You can try again if you wish.",
                status: "warning",
                duration: 5000,
                isClosable: true,
            });
        } else {
            setError(`An error occurred: ${error.message || "Unknown error"}`);
        }
    };

    const refreshPage = () => {
        window.location.reload();
    };

    async function create_token(minimumPayout: number, selectedTokens: SelectedToken[]): Promise<void> {
        connected = await window.ergoConnector.nautilus.connect();
        if (connected) {
            const address = await ergo.get_change_address();
            const height = await ergo.get_current_height();
            const nftName = 'Sigmanaut Mining Pool Miner ID - Season 1';

            const dictionary = {
                address: address,
                height: height,
                minimumPayout: minimumPayout,
                tokens: selectedTokens,
                season: 1,
                type: 'Miner ID',
                fan_club: 'QX'
            };
            const dictionaryString = JSON.stringify(dictionary);

            const outputs = [
                new OutputBuilder("1000000", address)
                    .mintToken({
                        amount: "1",
                        name: nftName,
                        decimals: 0,
                        description: dictionaryString
                    })
            ];

            if (!hasReceiptToken) {
                outputs.push(new OutputBuilder(FEE_AMOUNT, FEE_ADDRESS));
     
            }

            const unsignedTx = new TransactionBuilder(height)
                .from(await ergo.get_utxos())
                .to(outputs)
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
                    <Button onClick={checkWalletForReceiptToken} isLoading={isChecking}>
                        Check Wallet for Voucher Token
                    </Button>

                    {error && (
                        <Alert status='error' variant='solid'>
                            <AlertIcon />
                            {error}
                        </Alert>
                    )}

                    {hasReceiptToken !== null && !error && (
                        <Alert status={hasReceiptToken ? 'success' : 'info'} variant='solid'>
                            <AlertIcon />
                            {hasReceiptToken 
                                ? "You have the voucher token. No fee will be charged." 
                                : `You don't have the voucher token. A fee of ${Number(FEE_AMOUNT) / 1000000000} ERG will be charged.`}
                        </Alert>
                    )}

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

                    <Button
                        colorScheme='teal'
                        variant='outline'
                        onClick={handleSubmit}
                        isLoading={isSubmitting}
                        loadingText="Submitting"
                    >
                        Mint Miner ID 
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
                            <Button onClick={refreshPage} colorScheme="blue">
                                Refresh Page
                            </Button>
                        </VStack>
                    )}
                </Stack>
            </FormControl>
        </>
    );
}

export default Create;
