import hashlib

def md5_hash(text):
    """Compute the MD5 hash of a given string."""
    return hashlib.md5(text.encode()).hexdigest()

def find_matching_combinations(input_string, target_hashes):
    """Find single-character combinations of the input string that match any of the target hashes."""
    matches = {}  # Store matches in a dictionary: {hash: combination}
    
    # Iterate over each character in the input string
    for char in input_string:
        char_hash = md5_hash(char)
        if char_hash in target_hashes:
            matches[char_hash] = char
            # Stop if all target hashes have been matched
            if len(matches) == len(target_hashes):
                return matches
    return matches

def main():
    # Hardcoded input string and target hashes
    input_string = """
        Description and Deliverables
        This project offers students practical experience using a command shell to perform basic operations within Linux Operating System. 
        Specifically, you will learn to perform operations using remote access to connect to a different host computer, just like a hacker would should they obtain the necessary credentials and privileges after overtaking your machine :) 

        BEFORE STARTING PLEASE HAVE THESE PREPARED:

        Create a new directory in your CY2550 repository and call it "project1"
        Inside your project1 directory, create two text files:
        flags.txt - Put each flag in this file (one per line, order does not matter)
        token.txt - Put your token that you were emailed in this file
        Familiarize yourself with a screen-capturing tool of your choice. For Windows, you can use the built-in snipping tool or WIN+Shift+S. For Mac users, you can use the built-in snipping tool by pressing shift+command+3 to take a screenshot. 
        Steps to Complete The Project
        You must complete the following steps to receive full credit for this project. In addition, you will be required to submit a text file of flags you obtained for each level you completed. Only levels 8 and 9 will require a screenshot

        First, you will have to access the server, so your username will be your user portion of your Northeastern email.

        For example, the email: test@northeastern.edu will have the username test

        Your username and password will be located in my Khoury github repository under project1: here

        Next, you will have to login via SSH. Once you enter the command below, you should be prompted to enter a password, which will be the token you received via e-mail.

        ssh [username]@45.79.144.237 
        

        Descriptions and Commands of Interest

        In your home directory, you will have directories for each level. Please note that you may have to use some arguments with the commands
        Level 1: Easy Peasy Lemon Squeezy

        Simply just output the only file in the level :)
        Note that the flag format will be the same for the rest of the levels
        Commands of interest: man, ls, cd, cat
        Level 2: Spaces in names? Many directories? Explore around and find that pesky flag!

        Explore around the level directory and find that flag
        Did you know that the names of files are simply just strings?
        Commands of interest: man, ls, cd, cat, file
        Level 3: Where are the files? It can't be empty in here... Right...?

        Uh oh! There seems to be no files in the level directory? Is there really no files? Are they hiding? Are they not real? Find the hidden flag file
        Hint: There are files.
        Commands of interest: man, ls, cd, cat, file
        Level 4: There. Is. Too. Many. FILES.

        Great. We have to deal with about 1,000 files... NOT FUN. A lot of files are complete junk, while there is a random file that contains the flag. Find that file with the flag.
        Commands of interest: man, grep, ls, cd, cat, file, find
        Level 5: Which flag is not the imposter?

        flags.txt contains WAY too many flags... there can only be one unique flag... the rest of the flags are imposters... nothing suspicious here. Find the unique flag in flags.txt
        Commands of interest: man, grep, ls, sort, uniq, cat
        Level 6: Why did the hash go to the party? Because it heard they were serving hash browns!

        Ugh! the hashes directory contains too many hashes! I bet it's all MD5 hashes... Which directory holds the correct flag? Output the file in the correct directory to retrieve your flag
        Hint: What if there was some text you can hash??
        Commands of interest: man, sort, cat, md5sum, cd, ls
        Level 7: Found a lost file! Gotta contact their owner and group!

        Wow! About 400 random directories that can potentially contain the correct flag. Super fun! The correct flag is owned by justin and has group owner devin
        Commands of interest: man, ls, cd, find, file, grep, cat
        

        Reminder: Level 8 and Level 9 have no flags, but they require screenshots.

        Level 8: Bob? Who's Bob?

        Login as bob and take screenshots of the entire process
        This includes commands used, finding the credentials, logging in, and etc (Multiple screenshots is completely fine)
        Commands of interest: man, ls, cd, ssh
        Level 9: File transfer!

        Transfer a text file to your home directory (on the challenge server) and take screenshots of the entire process
        This includes commands used and showing that the file was successfully transferred (via ls)
        Commands of interest: man, scp
        scp requires a source and destination, which can be local to one machine, or on separate servers. These are in the format <user@ip_addr>:<path> with both parts being required conditionally. For instance
        scp /home/micah/important-document.txt justin@192.168.1.8:/etc/
        Will take the file importatn-document.txt from /home/micah on the machine this is executed on and transfer it to 192.168.1.8 as the user justin at the path /etc/important-document.txt
        

        Feel free to leverage Discord to ask questions. Please refrain from posting answers on Discord or sharing answers with your peers. Any act of academic dishonesty will not be tolerated. 

        

        Deliverables for Bandit Games:

        To receive full credit for this project, you must complete all nine levels.

        You should have:

        project1/flags.txt in your CY2550 repository
        This should have exactly 7 lines, one for each flag, and nothing else
        project1/token.txt in your CY2550 repository
        Submit this repository to Project 1 Bandit Games - Flag File
        a PDF containing all screenshots of solutions or image files containing solutions (one solution per image)
        Submit this to Project 1 Bandit Games - PDF/Images Submission
        Feel free to leverage Discord to ask questions. Please refrain from posting answers on Discord or sharing answers with your peers.

        Have fun! 

        This tool needs to be loaded in a new browser window
        """
    target_hashes = {
        "00c680a923c500f644e94e54cfd3ac14", "0fd4af589b31deb66fb462decddd07ab",
        "31c7b3c876f2145b42775f4afe325f22", "4b8c5ba5afbc5ab01ba51e9e58db1c2c",
        "6b128a53b8e23649dc4ce321fdaffb1c", "7e8704593ea4a18f9c107c130ec338b0",
        "8e08b0a5b28c1fcb2a45ac584aea111e", "a327ada4650d0d509f775a705f90ab21",
        "ba7cc27618894affc33bbb2dbbc009f8", "d422ac77bc724c327d06a3be17391f5d",
        "e2ab2c29eea3ae1dd7e25e8ee2befaff", "fed559e84f542dea1b33dab08f56f7ed",
        "04b1b33638b9f73dbd907ef65a5748a1", "10bce23ff210e396cdf364f73ab67d0d",
        "3a02fb75c5819a0bd8127f5ad35474bd", "5123ce0ccd1b609bf6a024264bf39261",
        "6bf6243f07e5f54bb79ee0825d223fd0", "81a88c11fb9ca8c952ba7793d126693b",
        "8fad48bafd4f604cfbcf9c825ac8ec93", "a37e48e7e443b64d82818bc21a700a59",
        "bbb9f1bfb5922f9f1059af7976a8a6aa", "d8f8b6a5a6501460d98e3acfe68d28f2",
        "e4dc2474421906bfed9be9af39e0533d", "0510609877f0db739caa8385c23512d2",
        "110351e86b6a515fb961bbd6433e7840", "3a2bfc574e21523efd19e1d416a559ce",
        "5403fe068f410a7a2ddc1fb32c9aed97", "6c4ea8d9fd0f7b8db6ad58d9e400e794",
        "81fe5a2f59c2a38b8ee82314a126c949", "90cd551c67b9ad9e6865c236688ba54a",
        "a819f014aaca7181085bef0e6855e8ce", "c25fc16e1f5eb22dfc3e6424ad81466a",
        "da3b5f5b2ff3ebeddc3ce519a79d696a", "e5b09cd4e9de9c57ccfb373849cb5fbc",
        "05a1c978d0bbb9d895a9a71518416041", "12571eea21c05a38d0a4f97bb95edc7a",
        "3d14d0213d2876cfd4a28655cf6ff2c8", "5531d33da078998cf250f1c61d083340",
        "6c9650f5b5cdb7e6b6f75534f9e50328", "82e6346c4d6f321e3bc89f491af8d654",
        "9171bfdbd8fd3d202e0c1f677a7ae4e3", "afd450b5d61d5e86f4aa151897fbd2b3",
        "c34bce2c1ba0e617a07885cd34f37332", "da9287be34eaa27acbfe52063935f498",
        "e920db858f407ac2022ead4ffb1ae80b", "06e84587cc72f00bf8232dce488e81c7",
        "16a194bc0e175c5679b4642fa2c31301", "4285aa270f9b5f126cff57f28c875f67",
        "559f2a9201dfdfcf4044c4280bc159d4", "6db69da73ae7c31105537409414d4f14",
        "84c5ed3a806b568d23407cfbff656ce7", "93007339c824053f821e370543fc8f60",
        "b0adabf85e2c5f94f46c9e79dfc259e7", "c5f2668b77374e4f42d40963eba4a1f9",
        "dadd531640b52b943f7584f0a5ab9cc8", "ebadc3ae5227fe6207a9c19d5f789bb3",
        "0725ddd77bfbe640b42b412f3085ec19", "1f364c030d289e416cf3d043df0ea28d",
        "459a4fa26ee6b3ebaecc7286372e6716", "61a0f42b2fedf87ab760823454b19368",
        "6ef3569392e46f6841701174a4cbe4f6", "87a4457725e99636858b584f3bc21b5a",
        "94862f18524efc577e16b1fe5dbb369b", "b1c6daa0645e7b46cb982190d5f2af6a",
        "c6f18b902aa6417499181f2fbddfe3b3", "ddb3516988d9ab208596b4553c071c22",
        "ed44355803bce97304db00b886b65f44", "08bc0642b61fc3391b51bf517f26a778",
        "20a91253906fc68d3e2bc3b045ceb422", "4743e0b06b698bb4a0a0f095047eec7c",
        "61d52b0b0189241d1e6bd0f7523612c1", "7066527399765d7ff804a5ef151f8d52",
        "87ffb18eef23d672335f390149a4b790", "948f4dca9742b6725361576580943141",
        "b35b8498aa64ddd21d7f9f09d5ee193b", "c9739f2f0a4b0136f56b18a5ea769a42",
        "de2da952ca930c55c1458b8e6f7a0dde", "ee3252976b520b07cab213639404a7c1",
        "0b9474e54b3e1b8a406ff6ada34a0515", "2b2e77fc13e25d5544d188c622a5cbd6",
        "48c10511c2392aa4fb8cdac3bc036521", "64e934347192e29a56b3f73e25dce289",
        "73f6b02d2a2de67d52d28d2e1b8f1bca", "89f8e31e3f14bec5e56c1edacc607178",
        "967f93bffe4dba712dcecf5b405c6b47", "b486b41378a476abd75809aab1026d1a",
        "ca9e991691fea2bdc8d2b1499f8682da", "e0ad812dc9730d992851212a0fef643e",
        "f1d9dbd1b0674b59e7da02c708dd0577", "0e58c53992b4318c2cb1258d6ba4e4a2",
        "2bc034feaf20b57d9b149d23fee61a82", "49f1477982307ed992580f764f878cbb",
        "6567ba31ac20d7a9cd6c1ed955061b2d", "78bf65ca2b1ed77d2129a865efe9bde5",
        "8c362d01d5f1457a3dce3a6142c21046", "9ab8908995a8bb684cb57e6c45337707",
        "b8f25ab96389bdcfd8011bd9f562c36b", "d2a551435b3d1631b1271df4f2f9fd6d",
        "e2427970014052dd85ea895a7aeb56d6", "f38f01e6836729ca3eb65275e4b0f2d6"
    }

    # Find matching combinations
    matches = find_matching_combinations(input_string, target_hashes)

    # Output the results
    if matches:
        print("Matches found:")
        for target_hash, combination in matches.items():
            print(f"Hash: {target_hash} -> Combination: {combination}")
    else:
        print("No matching combinations found.")

if __name__ == "__main__":
    main()


