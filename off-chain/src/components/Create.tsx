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

declare global {
    interface Window {
        ergoConnector: any;
    }
}
declare var ergo: any;
var connected: any;

function Create() {
    const [minimumPayout, setMinimumPayout] = useState<number>(0.51);
    const [created, setCreated] = useState<boolean>(false);
    const [tx, setTx] = useState<string>('...');
    const [error, setError] = useState<string>('');
    const [hasReceiptToken, setHasReceiptToken] = useState<boolean | null>(null);
    const [isChecking, setIsChecking] = useState<boolean>(false);
    const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
    const [voucherBurned, setVoucherBurned] = useState<boolean>(false);
    const [usingSigmaBytesAsVoucher, setUsingSigmaBytesAsVoucher] = useState<boolean>(false);
    const [voucherTokenId, setVoucherTokenId] = useState<string>('');
    const [payoutError, setPayoutError] = useState<string>('');
    const toast = useToast();

    // Define the receipt token ID and other constants
    const RECEIPT_TOKEN_ID = "ff9318934c9420f595f314eebc7188df7d8b4a7beb0fccc5b28e8ab272bb6e1b";
    const FEE_AMOUNT = "3000000000"; // 3 ERG in nanoERGs
    const FEE_ADDRESS ="9fA4RypzYiYNKHkcWjo1V2AYLA5Z3ny7bgVKBTdpQKrkaR38eJU";
    const MIN_PAYOUT = 0.51; // Minimum payout in ERG

    // Add collection ID constant
    const COLLECTION_ID = "10ba19fae939a8c185eddb239d85f4dc8a77564cb6167578d8019f24696446fc"; // Sigma Bytes Collection ID

    const handleMinimumPayoutChange = (valueAsString: string, valueAsNumber: number) => {
        if (isNaN(valueAsNumber)) {
            setPayoutError('Please enter a valid number');
            return;
        }
        
        if (valueAsNumber < MIN_PAYOUT) {
            setPayoutError(`Minimum payout must be at least ${MIN_PAYOUT} ERG`);
        } else {
            setPayoutError('');
        }
        
        setMinimumPayout(valueAsNumber);
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
            
            console.log("Current wallet address:", address);
            console.log("Looking for NFTs with collection ID:", COLLECTION_ID);

            const utxos = await ergo.get_utxos();
            if (!Array.isArray(utxos)) {
                throw new Error("Failed to retrieve UTXOs from the wallet.");
            }
            
            console.log(`Retrieved ${utxos.length} UTXOs from wallet`);

            console.log("Checking wallet for payment options...");
            
            // Check for Sigma Bytes NFTs first
            console.log("Checking for Sigma Bytes NFTs...");
            
            // Look for Sigma Bytes NFTs that match our criteria
            let validSigmaBytesNFT = null;
            let tokensChecked = 0;
            
            // Log all tokens in the wallet for debugging
            console.log("All tokens in wallet:");
            utxos.forEach((utxo: any, utxoIndex: number) => {
                if (utxo.assets && Array.isArray(utxo.assets)) {
                    utxo.assets.forEach((asset: any) => {
                        console.log(`UTXO ${utxoIndex} - Token ID: ${asset.tokenId}, Amount: ${asset.amount}`);
                    });
                }
            });
            
            // Function to get token info from Ergo Explorer API
            const getTokenInfo = async (tokenId: string) => {
                try {
                    const response = await fetch(`https://api.ergoplatform.com/api/v1/tokens/${tokenId}`);
                    if (!response.ok) {
                        console.log(`Failed to fetch token info for ${tokenId}: ${response.status}`);
                        return null;
                    }
                    const data = await response.json();
                    return {
                        name: data.name || "",
                        description: data.description || ""
                    };
                } catch (error) {
                    console.log(`Error fetching token info for ${tokenId}:`, error);
                    return null;
                }
            };
            
            for (const utxo of utxos) {
                if (utxo.assets && Array.isArray(utxo.assets)) {
                    for (const asset of utxo.assets) {
                        // Skip if not an NFT (amount must be 1)
                        if (asset.amount !== "1") {
                            console.log(`Skipping token ${asset.tokenId} - amount is ${asset.amount}, not 1`);
                            continue;
                        }
                        
                        tokensChecked++;
                        
                        try {
                            // Try to parse the token name and description
                            console.log(`Fetching token info for: ${asset.tokenId}`);
                            const tokenInfo = await getTokenInfo(asset.tokenId);
                            
                            if (!tokenInfo) {
                                console.log(`No token info found for ${asset.tokenId}`);
                                continue;
                            }
                            
                            console.log(`Token info for ${asset.tokenId}:`, tokenInfo);
                            console.log(`Checking token: ${asset.tokenId}, name: ${tokenInfo.name}`);
                            
                            // Check if it's a Sigma Bytes NFT
                            if (tokenInfo.name === "Sigma BYTES") {
                                console.log(`Found potential Sigma Bytes NFT: ${asset.tokenId}`);
                                
                                // Parse the description to check if it's from our collection
                                try {
                                    const description = JSON.parse(tokenInfo.description);
                                    console.log(`Token description: ${JSON.stringify(description)}`);
                                    
                                    // Log all criteria checks
                                    const collectionMatch = description.collection_id === COLLECTION_ID;
                                    
                                    // Check address - it might be stored in different formats or fields
                                    let addressMatch = false;
                                    if (description.address === address) {
                                        addressMatch = true;
                                    } else if (description.userAddress === address) {
                                        addressMatch = true;
                                    } else if (description.owner === address) {
                                        addressMatch = true;
                                    }
                                    
                                    // Check type - it might be stored in different formats or fields
                                    let typeMatch = false;
                                    if (description.type === "Pool Config") {
                                        typeMatch = true;
                                    } else if (description.nftType === "Pool Config") {
                                        typeMatch = true;
                                    } else if (description.tokenType === "Pool Config") {
                                        typeMatch = true;
                                    } else if (description.type && description.type.toLowerCase().includes("pool")) {
                                        typeMatch = true;
                                    }
                                    
                                    console.log("NFT criteria check:", {
                                        "collection_id in NFT": description.collection_id,
                                        "expected collection_id": COLLECTION_ID,
                                        "collection_match": collectionMatch,
                                        "address in NFT": description.address,
                                        "current address": address,
                                        "address_match": addressMatch,
                                        "type in NFT": description.type,
                                        "expected type": "Pool Config",
                                        "type_match": typeMatch
                                    });
                                    
                                    // Verify it's from our collection and owned by this user
                                    if (collectionMatch && addressMatch && typeMatch) {
                                        console.log("Valid Sigma Bytes NFT found that can be used as a voucher");
                                        validSigmaBytesNFT = asset.tokenId;
                                        break;
                                    } else {
                                        console.log("NFT doesn't meet criteria:", {
                                            "collection_match": collectionMatch,
                                            "address_match": addressMatch,
                                            "type_match": typeMatch
                                        });
                                    }
                                } catch (e) {
                                    console.log("Failed to parse NFT description", e);
                                    console.log("Raw description:", tokenInfo.description);
                                    continue;
                                }
                            }
                        } catch (e) {
                            console.log("Failed to get token info", e);
                            continue;
                        }
                    }
                }
                
                if (validSigmaBytesNFT) break;
            }
            
            console.log(`Checked ${tokensChecked} tokens for Sigma Bytes NFT criteria`);
            
            // If we found a valid Sigma Bytes NFT, use it
            if (validSigmaBytesNFT) {
                setHasReceiptToken(true);
                setUsingSigmaBytesAsVoucher(true);
                setVoucherTokenId(validSigmaBytesNFT);
                console.log(`Using Sigma Bytes NFT as voucher: ${validSigmaBytesNFT}`);
                console.log("This Sigma Bytes NFT will be burned during the minting process");
                return;
            } else {
                console.log("No valid Sigma Bytes NFT found that meets all criteria");
                
                // Fallback: Look for any Sigma Bytes NFT if strict criteria aren't met
                console.log("Trying fallback: Looking for any Sigma Bytes NFT...");
                let fallbackNFT = null;
                
                for (const utxo of utxos) {
                    if (utxo.assets && Array.isArray(utxo.assets)) {
                        for (const asset of utxo.assets) {
                            // Skip if not an NFT (amount must be 1)
                            if (asset.amount !== "1") continue;
                            
                            try {
                                const tokenInfo = await getTokenInfo(asset.tokenId);
                                if (!tokenInfo) continue;
                                
                                // Just check if it's a Sigma Bytes NFT by name
                                if (tokenInfo.name === "Sigma BYTES") {
                                    console.log(`Found Sigma Bytes NFT with fallback check: ${asset.tokenId}`);
                                    fallbackNFT = asset.tokenId;
                                    break;
                                }
                            } catch (e) {
                                continue;
                            }
                        }
                    }
                    
                    if (fallbackNFT) break;
                }
                
                if (fallbackNFT) {
                    console.log("Using fallback Sigma Bytes NFT as voucher");
                    setHasReceiptToken(true);
                    setUsingSigmaBytesAsVoucher(true);
                    setVoucherTokenId(fallbackNFT);
                    console.log(`Using Sigma Bytes NFT as voucher: ${fallbackNFT}`);
                    console.log("This Sigma Bytes NFT will be burned during the minting process");
                    return;
                } else {
                    console.log("No Sigma Bytes NFT found even with fallback check");
                }
            }
            
            // If no Sigma Bytes NFT, check for the original voucher token
            console.log("No valid Sigma Bytes NFT found. Checking for voucher tokens...");
            
            let voucherTokenCount = 0;
            utxos.forEach((utxo: any) => {
                if (utxo.assets && Array.isArray(utxo.assets)) {
                    utxo.assets.forEach((asset: any) => {
                        if (asset.tokenId === RECEIPT_TOKEN_ID) {
                            voucherTokenCount += parseInt(asset.amount);
                        }
                    });
                }
            });
            
            // If we have the original voucher token, use it
            if (voucherTokenCount > 0) {
                setHasReceiptToken(true);
                setUsingSigmaBytesAsVoucher(false);
                setVoucherTokenId(RECEIPT_TOKEN_ID);
                console.log(`Original voucher token found: ${voucherTokenCount} token(s)`);
                console.log("One voucher token will be burned during the minting process");
                return;
            }
            
            // If we get here, no valid payment options were found
            setHasReceiptToken(false);
            setUsingSigmaBytesAsVoucher(false);
            setVoucherTokenId('');
            console.log("No valid voucher tokens or Sigma Bytes NFTs found. Fee will be required.");
            
        } catch (error) {
            console.error("Error checking wallet:", error);
            setError(error instanceof Error ? error.message : "An unknown error occurred while checking the wallet.");
            setHasReceiptToken(null);
            setUsingSigmaBytesAsVoucher(false);
            setVoucherTokenId('');
        } finally {
            setIsChecking(false);
        }
    };

    const handleSubmit = async () => {
        if (hasReceiptToken === null) {
            setError('Please check your wallet for payment options first (Sigma Bytes NFT or voucher token).');
            return;
        }
        
        if (minimumPayout < MIN_PAYOUT) {
            setError(`Minimum payout must be at least ${MIN_PAYOUT} ERG`);
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
        } else if (error.message && error.message.includes("Voucher token")) {
            // Handle voucher token specific errors
            toast({
                title: "Voucher Token Error",
                description: error.message,
                status: "error",
                duration: 7000,
                isClosable: true,
            });
            setError(error.message);
        } else if (error.message && error.message.includes("Sigma Bytes NFT")) {
            // Handle Sigma Bytes NFT specific errors
            toast({
                title: "Sigma Bytes NFT Error",
                description: error.message,
                status: "error",
                duration: 7000,
                isClosable: true,
            });
            setError(error.message);
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
            try {
                const address = await ergo.get_change_address();
                const height = await ergo.get_current_height();
                const nftName = 'Sigma BYTES';
                
                // Define the getTokenInfo function
                const getTokenInfo = async (tokenId: string) => {
                    try {
                        const response = await fetch(`https://api.ergoplatform.com/api/v1/tokens/${tokenId}`);
                        if (!response.ok) {
                            console.log(`Failed to fetch token info for ${tokenId}: ${response.status}`);
                            return null;
                        }
                        const data = await response.json();
                        return {
                            name: data.name || "",
                            description: data.description || ""
                        };
                    } catch (error) {
                        console.log(`Error fetching token info for ${tokenId}:`, error);
                        return null;
                    }
                };
                
                const dictionary = {
                    address: address,
                    height: height,
                    minimumPayout: minimumPayout,
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

                const utxos = await ergo.get_utxos();
                console.log("DEBUG - All UTXOs:", JSON.stringify(utxos));
                
                let txBuilder;
                
                if (hasReceiptToken) {
                    // If user has a voucher token or Sigma Bytes NFT, burn it
                    // Find a UTXO containing the selected token
                    const voucherUtxo = utxos.find((utxo: any) => 
                        utxo.assets && Array.isArray(utxo.assets) && 
                        utxo.assets.some((asset: any) => 
                            asset.tokenId === voucherTokenId && parseInt(asset.amount) > 0
                        )
                    );
                    
                    if (!voucherUtxo) {
                        throw new Error(`${usingSigmaBytesAsVoucher ? "Sigma Bytes NFT" : "Voucher token"} not found in wallet. Please try again.`);
                    }
                    
                    console.log(`DEBUG - Found ${usingSigmaBytesAsVoucher ? "Sigma Bytes NFT" : "voucher token"} UTXO:`, JSON.stringify(voucherUtxo));
                    
                    // Find the token in the UTXO
                    const voucherToken = voucherUtxo.assets.find((asset: any) => 
                        asset.tokenId === voucherTokenId
                    );
                    
                    if (!voucherToken) {
                        throw new Error(`${usingSigmaBytesAsVoucher ? "Sigma Bytes NFT" : "Voucher token"} not found in the selected UTXO. Please try again.`);
                    }
                    
                    console.log(`DEBUG - Token details: tokenId=${voucherToken.tokenId}, amount=${voucherToken.amount}`);
                    
                    // If using Sigma Bytes NFT, verify it again to ensure it's valid
                    if (usingSigmaBytesAsVoucher) {
                        try {
                            // Use our custom function for verification
                            const tokenInfo = await getTokenInfo(voucherTokenId);
                            if (!tokenInfo || tokenInfo.name !== "Sigma BYTES") {
                                throw new Error("Invalid Sigma Bytes NFT. Please try again.");
                            }
                            
                            // For the second verification, we'll be more lenient and just check the name
                            console.log("Sigma Bytes NFT verified again before burning (name check only)");
                            
                            // Try to parse the description but don't fail if it doesn't match exactly
                            try {
                                const description = JSON.parse(tokenInfo.description);
                                console.log("NFT description for burning:", description);
                            } catch (e) {
                                console.log("Could not parse NFT description, but proceeding anyway");
                            }
                        } catch (e) {
                            console.error("Error verifying Sigma Bytes NFT:", e);
                            throw new Error("Failed to verify Sigma Bytes NFT: " + (e instanceof Error ? e.message : "Unknown error"));
                        }
                    }
                    
                    // Create a transaction builder that explicitly burns the token
                    txBuilder = new TransactionBuilder(height)
                        .from(utxos)
                        .to(outputs)
                        .burnTokens([{ 
                            tokenId: voucherTokenId, 
                            amount: "1" 
                        }])
                        .sendChangeTo(address)
                        .payMinFee();
                    
                    console.log(`One ${usingSigmaBytesAsVoucher ? "Sigma Bytes NFT" : "voucher token"} will be burned in this transaction using burnTokens method`);
                    setVoucherBurned(true);
                } else {
                    // Standard transaction without burning tokens
                    txBuilder = new TransactionBuilder(height)
                        .from(utxos)
                        .to(outputs)
                        .sendChangeTo(address)
                        .payMinFee();
                }
                
                const unsignedTx = txBuilder.build().toEIP12Object();

                // Final validation check
                if (hasReceiptToken) {
                    console.log(`DEBUG - Validating transaction for ${usingSigmaBytesAsVoucher ? "Sigma Bytes NFT" : "voucher token"} burning`);
                    
                    // Check if the transaction is properly constructed for burning the token
                    const inputTokens = unsignedTx.inputs.flatMap((input: any) => 
                        input.assets ? input.assets.filter((asset: any) => asset.tokenId === voucherTokenId) : []
                    );
                    
                    const outputTokens = unsignedTx.outputs.flatMap((output: any) => 
                        output.assets ? output.assets.filter((asset: any) => asset.tokenId === voucherTokenId) : []
                    );
                    
                    console.log("DEBUG - Input tokens:", JSON.stringify(inputTokens));
                    console.log("DEBUG - Output tokens:", JSON.stringify(outputTokens));
                    
                    // Check if the transaction includes the token in its inputs
                    if (inputTokens.length === 0) {
                        console.log("DEBUG - No tokens found in inputs");
                        console.log("DEBUG - All inputs:", JSON.stringify(unsignedTx.inputs));
                        
                        throw new Error(`${usingSigmaBytesAsVoucher ? "Sigma Bytes NFT" : "Voucher token"} not found in transaction inputs. Please try again.`);
                    }
                    
                    // Calculate total input and output amounts
                    const totalInputAmount = inputTokens.reduce((sum: number, token: any) => sum + parseInt(token.amount), 0);
                    const totalOutputAmount = outputTokens.reduce((sum: number, token: any) => sum + parseInt(token.amount), 0);
                    
                    console.log(`DEBUG - Total input amount: ${totalInputAmount}`);
                    console.log(`DEBUG - Total output amount: ${totalOutputAmount}`);
                    console.log(`DEBUG - Difference (tokens being burned): ${totalInputAmount - totalOutputAmount}`);
                    
                    // Ensure exactly one token is being burned
                    if (totalInputAmount <= totalOutputAmount) {
                        console.log("DEBUG - Error condition: totalInputAmount <= totalOutputAmount");
                        console.log(`DEBUG - Input UTXOs:`, JSON.stringify(unsignedTx.inputs));
                        console.log(`DEBUG - Output UTXOs:`, JSON.stringify(unsignedTx.outputs));
                        throw new Error(`No ${usingSigmaBytesAsVoucher ? "Sigma Bytes NFT" : "voucher token"} is being burned. Please try again.`);
                    }
                    
                    if (totalInputAmount - totalOutputAmount !== 1) {
                        throw new Error(`Expected to burn exactly 1 ${usingSigmaBytesAsVoucher ? "Sigma Bytes NFT" : "voucher token"}, but ${totalInputAmount - totalOutputAmount} would be burned.`);
                    }
                    
                    console.log(`Transaction validation successful: One ${usingSigmaBytesAsVoucher ? "Sigma Bytes NFT" : "voucher token"} will be burned`);
                }

                const signedTx = await ergo.sign_tx(unsignedTx);
                const txId = await ergo.submit_tx(signedTx);
                setTx(txId);
                setCreated(true);
            } catch (error) {
                console.error("Error in create_token:", error);
                throw error;
            }
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
            maxW="100%"
            width="100%"
            mx="auto"
        >
            <VStack spacing={8} align="stretch">
                <Heading
                    as="h1"
                    size="2xl"
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
                    fontSize="lg"
                    mb={4}
                >
                    Sigmanauts Mining Pool Configuration NFT
                </Text>

                <Box
                    borderRadius="lg"
                    overflow="hidden"
                    position="relative"
                    bg="gray.900"
                    p={6}
                >
                    <Flex justify="flex-start" align="center" mb={4}>
                        <Text color="cyan.400" fontSize="md">Gen: 1.0.0</Text>
                    </Flex>

                    {error && (
                        <Alert status='error' variant='solid' bg="red.900" color="white" fontSize="md" py={4}>
                            <AlertIcon boxSize={5} />
                            {error}
                        </Alert>
                    )}

                    {hasReceiptToken !== null && !error && (
                        <Alert
                            status={hasReceiptToken ? 'success' : 'info'}
                            variant='solid'
                            bg={hasReceiptToken ? "green.900" : "blue.900"}
                            color="white"
                            fontSize="md"
                            py={4}
                        >
                            <AlertIcon boxSize={5} />
                            {hasReceiptToken 
                                ? usingSigmaBytesAsVoucher 
                                    ? "Sigma Bytes NFT verified - This NFT will be burned during minting" 
                                    : "Voucher token verified - One token will be burned during minting"
                                : `No free minting options found - Required fee: ${Number(FEE_AMOUNT) / 1000000000} ERG`}
                        </Alert>
                    )}

                    <FormControl mt={6} isInvalid={!!payoutError}>
                        <FormLabel color="whiteAlpha.900" fontSize="lg">Set Minimum Payout (ERG)</FormLabel>
                        <NumberInput
                            min={MIN_PAYOUT}
                            value={minimumPayout}
                            onChange={handleMinimumPayoutChange}
                            precision={4}
                            step={0.01}
                            bg="whiteAlpha.100"
                            borderRadius="md"
                            size="lg"
                        >
                            <NumberInputField color="white" fontSize="lg" height="60px" />
                            <NumberInputStepper>
                                <NumberIncrementStepper color="whiteAlpha.800" />
                                <NumberDecrementStepper color="whiteAlpha.800" />
                            </NumberInputStepper>
                        </NumberInput>
                        {payoutError && (
                            <Text color="red.300" fontSize="sm" mt={1}>
                                {payoutError}
                            </Text>
                        )}
                    </FormControl>

                    <VStack spacing={6} mt={8}>
                        <Button
                            w="full"
                            onClick={checkWalletForReceiptToken}
                            isLoading={isChecking}
                            bgGradient="linear(to-r, purple.600, blue.600)"
                            color="white"
                            _hover={{
                                bgGradient: "linear(to-r, purple.700, blue.700)",
                            }}
                            size="lg"
                            height="60px"
                            fontSize="lg"
                        >
                            Check Payment Options
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
                            size="lg"
                            height="60px"
                            fontSize="lg"
                        >
                            MINT NOW • {hasReceiptToken 
                                ? usingSigmaBytesAsVoucher 
                                    ? 'Burn Sigma Bytes NFT' 
                                    : 'Burn 1 Voucher' 
                                : `${Number(FEE_AMOUNT) / 1000000000} ERG`}
                        </Button>
                    </VStack>

                    {created && (
                        <VStack spacing={4} mt={6}>
                            <Alert
                                status='success'
                                variant='solid'
                                bg="green.900"
                                color="white"
                                fontSize="md"
                                py={4}
                            >
                                <AlertIcon boxSize={5} />
                                {voucherBurned 
                                    ? usingSigmaBytesAsVoucher
                                        ? "Sigma Bytes NFT Successfully Minted! Your existing Sigma Bytes NFT has been burned."
                                        : "Sigma Bytes NFT Successfully Minted! Your voucher token has been burned."
                                    : "Sigma Bytes NFT Successfully Minted!"}
                            </Alert>
                            <Link
                                href={`https://ergexplorer.com/transactions/${tx}`}
                                isExternal
                                color="cyan.400"
                                _hover={{ color: "cyan.300" }}
                                fontSize="lg"
                            >
                                View on Explorer
                            </Link>
                        </VStack>
                    )}
                </Box>

                <Text
                    textAlign="center"
                    color="whiteAlpha.700"
                    fontSize="md"
                    mt={4}
                >
                    Each Sigma Bytes NFT allows configuration of minimum payout settings for the Sigmanauts Mining Pool.
                </Text>

                <Text
                    textAlign="center"
                    color="whiteAlpha.700"
                    fontSize="md"
                    mt={2}
                >
                    You can mint with an existing Sigma Bytes NFT, a voucher token, or pay a {Number(FEE_AMOUNT) / 1000000000} ERG fee.
                </Text>
            </VStack>
        </Box>
    );
}

export default Create;
