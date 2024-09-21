import React from 'react';

import { 
    Box, 
    Divider,
    Text,
    useColorModeValue,
} from '@chakra-ui/react'

interface TokenProps {
    title?: string;
}

function Header({ title }: TokenProps) {

    const color = useColorModeValue('gray.300', 'gray.600')

    return (
        <>
            <Box textAlign={'right'}>
            <Text 
                fontSize='50px' 
                color={color}>
                {title}
            </Text>
                <Divider mb={5} />
            </Box>
        
        </>
    );
};

export default Header;
