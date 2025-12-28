"""
Author: Saradindu Sengupta
Email: saradindu.mi1@iiitmk.ac.in
Date: 2025-12-28 05:43:47
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from logging import INFO
from typing import Optional

from dotenv import load_dotenv

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF
from graphiti_core.llm_client.errors import RateLimitError

#################################################
# CONFIGURATION
#################################################
# Set up logging and environment variables for
# connecting to Neo4j database
#################################################

# Configure logging
logging.basicConfig(
    level=INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

if(False):
    # Neo4j connection parameters
    # Make sure Neo4j Desktop is running with a local DBMS started
    load_dotenv()
    neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://0.0.0.0:7687')
    neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
    neo4j_password = os.environ.get('NEO4J_PASSWORD', 'password')

neo4j_uri = 'bolt://localhost:7687'
neo4j_user = 'neo4j'
neo4j_password = 'dev_password_123'

if not neo4j_uri or not neo4j_user or not neo4j_password:
    raise ValueError('NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD must be set')

# Check for OpenAI API key
openai_api_key = os.environ.get('OPENAI_API_KEY')
if not openai_api_key:
    logger.error('OPENAI_API_KEY not found in environment variables')
    logger.error('Please set your OpenAI API key or check your quota at: https://platform.openai.com/account/billing')
    sys.exit(1)

logger.info(f'Using OpenAI API key: {openai_api_key[:8]}...')


async def add_episode_with_retry(
    graphiti: Graphiti,
    name: str,
    episode_body: str,
    source: EpisodeType,
    source_description: str,
    reference_time: datetime,
    max_retries: int = 3,
    base_delay: float = 2.0,
) -> bool:
    """Add an episode with exponential backoff retry logic for rate limit errors.
    
    Args:
        graphiti: Graphiti instance
        name: Episode name
        episode_body: Episode content
        source: Episode type
        source_description: Episode description
        reference_time: Reference timestamp
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
        
    Returns:
        True if successful, False otherwise
    """
    for attempt in range(max_retries):
        try:
            await graphiti.add_episode(
                name=name,
                episode_body=episode_body,
                source=source,
                source_description=source_description,
                reference_time=reference_time,
            )
            logger.info(f'Successfully added episode: {name}')
            return True
            
        except RateLimitError as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(
                    f'Rate limit hit for {name}. Retrying in {delay:.1f}s... '
                    f'(Attempt {attempt + 1}/{max_retries})'
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f'Failed to add episode {name} after {max_retries} attempts due to rate limiting.'
                )
                logger.error(
                    'OpenAI API quota exceeded. Please check your plan and billing at: '
                    'https://platform.openai.com/account/billing'
                )
                return False
                
        except Exception as e:
            logger.error(f'Unexpected error adding episode {name}: {type(e).__name__}: {e}')
            return False
            
    return False


async def main():
    #################################################
    # INITIALIZATION
    #################################################
    # Connect to Neo4j and set up Graphiti indices
    # This is required before using other Graphiti
    # functionality
    #################################################

    # Initialize Graphiti with Neo4j connection
    graphiti = Graphiti(neo4j_uri, neo4j_user, neo4j_password)
    
    # Track success/failure statistics
    episodes_added = 0
    episodes_failed = 0

    try:
        #################################################
        # ADDING EPISODES
        #################################################
        # Episodes are the primary units of information
        # in Graphiti. They can be text or structured JSON
        # and are automatically processed to extract entities
        # and relationships.
        #################################################

        # Example: Add Episodes
        # Episodes list containing both text and JSON episodes
        episodes = [
            {
                'content': 'Kamala Harris is the Attorney General of California. She was previously '
                'the district attorney for San Francisco.',
                'type': EpisodeType.text,
                'description': 'podcast transcript',
            },
            {
                'content': 'As AG, Harris was in office from January 3, 2011 – January 3, 2017',
                'type': EpisodeType.text,
                'description': 'podcast transcript',
            },
            {
                'content': {
                    'name': 'Gavin Newsom',
                    'position': 'Governor',
                    'state': 'California',
                    'previous_role': 'Lieutenant Governor',
                    'previous_location': 'San Francisco',
                },
                'type': EpisodeType.json,
                'description': 'podcast metadata',
            },
            {
                'content': {
                    'name': 'Gavin Newsom',
                    'position': 'Governor',
                    'term_start': 'January 7, 2019',
                    'term_end': 'Present',
                },
                'type': EpisodeType.json,
                'description': 'podcast metadata',
            },
        ]

        # Add episodes to the graph with retry logic and rate limiting
        logger.info(f'Starting to add {len(episodes)} episodes...')
        
        for i, episode in enumerate(episodes):
            episode_name = f'Freakonomics Radio {i}'
            episode_body = (
                episode['content']
                if isinstance(episode['content'], str)
                else json.dumps(episode['content'])
            )
            
            logger.info(f'Processing episode {i+1}/{len(episodes)}: {episode_name}')
            
            success = await add_episode_with_retry(
                graphiti=graphiti,
                name=episode_name,
                episode_body=episode_body,
                source=episode['type'],
                source_description=episode['description'],
                reference_time=datetime.now(timezone.utc),
                max_retries=3,
                base_delay=2.0,
            )
            
            if success:
                episodes_added += 1
                print(f'✓ Added episode: {episode_name} ({episode["type"].value})')
                # Add a small delay between episodes to avoid rate limiting
                if i < len(episodes) - 1:  # Don't delay after the last episode
                    await asyncio.sleep(1.0)
            else:
                episodes_failed += 1
                print(f'✗ Failed to add episode: {episode_name}')
                logger.error('Consider reducing the number of episodes or upgrading your OpenAI plan')
                # Stop processing if we hit rate limits
                logger.warning('Stopping episode processing due to rate limit errors')
                break
        
        logger.info(
            f'Episode processing complete. Added: {episodes_added}, Failed: {episodes_failed}'
        )

        #################################################
        # BASIC SEARCH
        #################################################
        # The simplest way to retrieve relationships (edges)
        # from Graphiti is using the search method, which
        # performs a hybrid search combining semantic
        # similarity and BM25 text retrieval.
        #################################################

        # Only proceed with searches if we successfully added episodes
        if episodes_added == 0:
            logger.warning('No episodes were added successfully. Skipping search operations.')
            return
            
        # Perform a hybrid search combining semantic similarity and BM25 retrieval
        print("\nSearching for: 'Who was the California Attorney General?'")
        try:
            results = await graphiti.search('Who was the California Attorney General?')
        except RateLimitError:
            logger.error('Rate limit hit during search. Skipping search operations.')
            return
        except Exception as e:
            logger.error(f'Error during search: {type(e).__name__}: {e}')
            return

        # Print search results
        print('\nSearch Results:')
        for result in results:
            print(f'UUID: {result.uuid}')
            print(f'Fact: {result.fact}')
            if hasattr(result, 'valid_at') and result.valid_at:
                print(f'Valid from: {result.valid_at}')
            if hasattr(result, 'invalid_at') and result.invalid_at:
                print(f'Valid until: {result.invalid_at}')
            print('---')

        #################################################
        # CENTER NODE SEARCH
        #################################################
        # For more contextually relevant results, you can
        # use a center node to rerank search results based
        # on their graph distance to a specific node
        #################################################

        # Use the top search result's UUID as the center node for reranking
        if results and len(results) > 0:
            # Get the source node UUID from the top result
            center_node_uuid = results[0].source_node_uuid

            print('\nReranking search results based on graph distance:')
            print(f'Using center node UUID: {center_node_uuid}')

            try:
                reranked_results = await graphiti.search(
                    'Who was the California Attorney General?', center_node_uuid=center_node_uuid
                )
            except RateLimitError:
                logger.error('Rate limit hit during reranked search. Skipping.')
                return
            except Exception as e:
                logger.error(f'Error during reranked search: {type(e).__name__}: {e}')
                return

            # Print reranked search results
            print('\nReranked Search Results:')
            for result in reranked_results:
                print(f'UUID: {result.uuid}')
                print(f'Fact: {result.fact}')
                if hasattr(result, 'valid_at') and result.valid_at:
                    print(f'Valid from: {result.valid_at}')
                if hasattr(result, 'invalid_at') and result.invalid_at:
                    print(f'Valid until: {result.invalid_at}')
                print('---')
        else:
            print('No results found in the initial search to use as center node.')

        #################################################
        # NODE SEARCH USING SEARCH RECIPES
        #################################################
        # Graphiti provides predefined search recipes
        # optimized for different search scenarios.
        # Here we use NODE_HYBRID_SEARCH_RRF for retrieving
        # nodes directly instead of edges.
        #################################################

        # Example: Perform a node search using _search method with standard recipes
        print(
            '\nPerforming node search using _search method with standard recipe NODE_HYBRID_SEARCH_RRF:'
        )

        # Use a predefined search configuration recipe and modify its limit
        node_search_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
        node_search_config.limit = 5  # Limit to 5 results

        # Execute the node search
        try:
            node_search_results = await graphiti._search(
                query='California Governor',
                config=node_search_config,
            )
        except RateLimitError:
            logger.error('Rate limit hit during node search. Skipping.')
            return
        except Exception as e:
            logger.error(f'Error during node search: {type(e).__name__}: {e}')
            return

        # Print node search results
        print('\nNode Search Results:')
        for node in node_search_results.nodes:
            print(f'Node UUID: {node.uuid}')
            print(f'Node Name: {node.name}')
            node_summary = node.summary[:100] + '...' if len(node.summary) > 100 else node.summary
            print(f'Content Summary: {node_summary}')
            print(f'Node Labels: {", ".join(node.labels)}')
            print(f'Created At: {node.created_at}')
            if hasattr(node, 'attributes') and node.attributes:
                print('Attributes:')
                for key, value in node.attributes.items():
                    print(f'  {key}: {value}')
            print('---')

    finally:
        #################################################
        # CLEANUP
        #################################################
        # Always close the connection to Neo4j when
        # finished to properly release resources
        #################################################

        # Close the connection
        await graphiti.close()
        print('\nConnection closed')


if __name__ == '__main__':
    asyncio.run(main())
