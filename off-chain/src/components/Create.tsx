import React, { useState } from 'react';
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
    VStack,
    Link,
    useToast,
    Box,
    Text,
    Flex,
    Heading,
} from '@chakra-ui/react';
import { OutputBuilder, TransactionBuilder } from "@fleet-sdk/core";
import Title from '../components/Title';
import CryptoJS from 'crypto-js';

declare global {
    interface Window {
        ergoConnector: any;
    }
}
declare var ergo: any;
var connected: any;

function Create() {
    const [minimumPayout, setMinimumPayout] = useState<number>(0.01);
    const [created, setCreated] = useState<boolean>(false);
    const [tx, setTx] = useState<string>('...');
    const [error, setError] = useState<string>('');
    const [hasReceiptToken, setHasReceiptToken] = useState<boolean | null>(null);
    const [isChecking, setIsChecking] = useState<boolean>(false);
    const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
    const toast = useToast();

    // Define the receipt token ID and other constants
    const RECEIPT_TOKEN_ID = "ff9318934c9420f595f314eebc7188df7d8b4a7beb0fccc5b28e8ab272bb6e1b";
    const FEE_AMOUNT = "3000000000"; // 3 ERG in nanoERGs
    const FEE_ADDRESS ="9fA4RypzYiYNKHkcWjo1V2AYLA5Z3ny7bgVKBTdpQKrkaR38eJU";

    // Add collection ID constant
    const COLLECTION_ID = "10ba19fae939a8c185eddb239d85f4dc8a77564cb6167578d8019f24696446fc"; // Sigma Bytes Collection ID

    const handleMinimumPayoutChange = (valueAsString: string, valueAsNumber: number) => {
        setMinimumPayout(valueAsNumber);
    };

    // Function to encrypt the payout value
    const encryptPayout = (payout: number): string => {
        const secretKey = 'your-secret-key'; // In production, use a secure key management system
        return CryptoJS.AES.encrypt(payout.toString(), secretKey).toString();
    };

    // Function to decrypt the payout value (for authorized parties)
    const decryptPayout = (encryptedPayout: string): number => {
        const secretKey = 'your-secret-key';
        const decrypted = CryptoJS.AES.decrypt(encryptedPayout, secretKey);
        return parseFloat(decrypted.toString(CryptoJS.enc.Utf8));
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
        if (hasReceiptToken === null) {
            setError('Please check your wallet for the voucher token first.');
            return;
        }
        try {
            setIsSubmitting(true);
            await create_token(minimumPayout);
        } catch (error) {
            handleTransactionError(error);
        } finally {
            setIsSubmitting(false);
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

    async function create_token(minimumPayout: number): Promise<void> {
        connected = await window.ergoConnector.nautilus.connect();
        if (connected) {
            const address = await ergo.get_change_address();
            const height = await ergo.get_current_height();
            const nftName = 'Sigma BYTES';

            const encryptedPayout = encryptPayout(minimumPayout);
            
            const dictionary = {
                address: address,
                height: height,
                encryptedPayout: encryptedPayout,
                season: 1,
                type: 'Pool Config',
                collection_id: COLLECTION_ID,
                description: 'Sigmanauts Mining Pool Configuration Token'
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
        <Box
            p={6}
            borderRadius="xl"
            bg="rgba(13, 17, 23, 0.95)"
            borderWidth="1px"
            borderColor="rgba(99, 179, 237, 0.3)"
            boxShadow="0 0 20px rgba(99, 179, 237, 0.2)"
            maxW="600px"
            mx="auto"
        >
            <VStack spacing={6} align="stretch">
                <Heading
                    as="h1"
                    size="xl"
                    textAlign="center"
                    bgGradient="linear(to-r, #ff69b4, #4299e1)"
                    bgClip="text"
                    fontWeight="extrabold"
                    letterSpacing="wider"
                >
                    SIGMA BYTES
                </Heading>
                
                <Text
                    textAlign="center"
                    color="whiteAlpha.800"
                    fontSize="md"
                    mb={4}
                >
                    Sigmanauts Mining Pool Configuration NFT
                </Text>

                <Box
                    borderRadius="lg"
                    overflow="hidden"
                    position="relative"
                    bg="gray.900"
                    p={4}
                >
                    <Flex justify="flex-start" align="center" mb={4}>
                        <Text color="cyan.400" fontSize="sm">Gen: 1.0.0</Text>
                    </Flex>

                    {error && (
                        <Alert status='error' variant='solid' bg="red.900" color="white">
                            <AlertIcon />
                            {error}
                        </Alert>
                    )}

                    {hasReceiptToken !== null && !error && (
                        <Alert
                            status={hasReceiptToken ? 'success' : 'info'}
                            variant='solid'
                            bg={hasReceiptToken ? "green.900" : "blue.900"}
                            color="white"
                        >
                            <AlertIcon />
                            {hasReceiptToken 
                                ? "Voucher token verified - No fee required" 
                                : `Required fee: ${Number(FEE_AMOUNT) / 1000000000} ERG`}
                        </Alert>
                    )}

                    <FormControl mt={4}>
                        <FormLabel color="whiteAlpha.900">Set Minimum Payout (ERG)</FormLabel>
                        <NumberInput
                            min={0}
                            value={minimumPayout}
                            onChange={handleMinimumPayoutChange}
                            precision={2}
                            step={0.01}
                            bg="whiteAlpha.100"
                            borderRadius="md"
                        >
                            <NumberInputField color="white" />
                            <NumberInputStepper>
                                <NumberIncrementStepper color="whiteAlpha.800" />
                                <NumberDecrementStepper color="whiteAlpha.800" />
                            </NumberInputStepper>
                        </NumberInput>
                    </FormControl>

                    <VStack spacing={4} mt={6}>
                        <Button
                            w="full"
                            onClick={checkWalletForReceiptToken}
                            isLoading={isChecking}
                            bgGradient="linear(to-r, purple.600, blue.600)"
                            color="white"
                            _hover={{
                                bgGradient: "linear(to-r, purple.700, blue.700)",
                            }}
                        >
                            Verify Wallet
                        </Button>

                        <Button
                            w="full"
                            onClick={handleSubmit}
                            isLoading={isSubmitting}
                            loadingText="Minting..."
                            bgGradient="linear(to-r, pink.500, purple.500)"
                            color="white"
                            _hover={{
                                bgGradient: "linear(to-r, pink.600, purple.600)",
                            }}
                        >
                            MINT NOW • {hasReceiptToken ? '0' : (Number(FEE_AMOUNT) / 1000000000)} ERG
                        </Button>
                    </VStack>

                    {created && (
                        <VStack spacing={4} mt={6}>
                            <Alert
                                status='success'
                                variant='solid'
                                bg="green.900"
                                color="white"
                            >
                                <AlertIcon />
                                Sigma Bytes NFT Successfully Minted!
                            </Alert>
                            <Link
                                href={`https://ergexplorer.com/transactions/${tx}`}
                                isExternal
                                color="cyan.400"
                                _hover={{ color: "cyan.300" }}
                            >
                                View on Explorer
                            </Link>
                        </VStack>
                    )}
                </Box>

                <Text
                    textAlign="center"
                    color="whiteAlpha.700"
                    fontSize="sm"
                    mt={4}
                >
                    Each Sigma Bytes NFT allows configuration of minimum payout settings for the Sigmanauts Mining Pool.
                </Text>
            </VStack>
        </Box>
    );
}

export default Create;
